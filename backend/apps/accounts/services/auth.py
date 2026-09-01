from datetime import timedelta

from apps.accounts.models import OTPVerification, User
from apps.accounts.services.otp import (
    challenge_send_count,
    can_resend,
    check_and_increment_ip_rate_limit,
    generate_otp,
    hash_otp,
    invalidate_previous_challenges,
    is_expired,
    store_otp_code,
)
from apps.accounts.services.phone import normalize_phone_number
from apps.accounts.tasks import send_otp_sms_task
from apps.security.models import LoginHistory, SecurityEvent
from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import (
    AuthenticationFailed,
    PermissionDenied,
    Throttled,
)
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:
    @staticmethod
    def normalize_phone(phone_number):
        return normalize_phone_number(phone_number)

    @staticmethod
    def request_otp(phone_number, purpose, request_ip=None, user_agent=""):
        normalized_phone = normalize_phone_number(phone_number)

        ip_limit = check_and_increment_ip_rate_limit(request_ip)

        if not ip_limit["allowed"]:
            raise Throttled(
                detail=(
                    "Too many OTP requests from this IP. "
                    "Please try again later."
                ),
                wait=ip_limit["retry_after"],
            )

        account_exists = User.objects.filter(
            phone_number=normalized_phone
        ).exists()

        if purpose == "login" and not account_exists:
            return {
                "allowed": False,
                "account_exists": False,
                "next_step": "registration",
                "phone_number": normalized_phone,
            }

        if purpose == "registration" and account_exists:
            return {
                "allowed": False,
                "account_exists": True,
                "message": "This phone number already has an account.",
                "next_step": "login",
                "phone_number": normalized_phone,
            }

        if not can_resend(normalized_phone, purpose):
            raise PermissionDenied(
                "Please wait before requesting a new OTP."
            )

        if (
                challenge_send_count(
                    normalized_phone,
                    purpose,
                )
                >= settings.OTP_MAX_SENDS
        ):
            raise PermissionDenied(
                "Too many OTP requests. Please try again later."
            )

        invalidate_previous_challenges(
            normalized_phone,
            purpose,
        )

        code = generate_otp()

        challenge = OTPVerification.objects.create(
            phone_number=normalized_phone,
            purpose=purpose,
            code_hash=hash_otp(code),
            expires_at=(
                    timezone.now()
                    + timedelta(
                seconds=settings.OTP_TTL_SECONDS
            )
            ),
            max_attempts=settings.OTP_MAX_ATTEMPTS,
            request_ip=request_ip,
            user_agent=user_agent[:500],
        )

        store_otp_code(
            challenge.id,
            code,
            settings.OTP_TTL_SECONDS,
        )

        transaction.on_commit(
            lambda: send_otp_sms_task.delay(challenge.id)
        )

        SecurityEvent.objects.create(
            user=None,
            event_type="otp_requested",
            description=(
                f"OTP requested for "
                f"{normalized_phone} ({purpose})"
            ),
            ip_address=request_ip,
        )

        return {
            "allowed": True,
            "challenge_id": str(challenge.id),
            "expires_in": settings.OTP_TTL_SECONDS,
            "resend_available_in": (
                settings.OTP_RESEND_COOLDOWN_SECONDS
            ),
            "next_step": "otp",
            "account_exists": account_exists,
        }

    @staticmethod
    def verify_otp(
            challenge_id,
            otp,
            request_ip=None,
            user_agent="",
    ):
        try:
            challenge_id = int(challenge_id)
        except (TypeError, ValueError):
            raise ValidationError(
                "Invalid verification challenge."
            )

        if challenge_id <= 0:
            raise ValidationError(
                "Invalid verification challenge."
            )

        otp = str(otp or "").strip()

        if not otp.isdigit() or len(otp) != 6:
            raise ValidationError("Invalid OTP.")

        try:
            challenge = OTPVerification.objects.get(
                id=challenge_id
            )
        except OTPVerification.DoesNotExist as exc:
            raise ValidationError(
                "Invalid verification challenge."
            ) from exc

        if challenge.is_used:
            raise ValidationError(
                "This OTP challenge has already been used."
            )

        if is_expired(challenge):
            challenge.is_used = True
            challenge.save(update_fields=["is_used"])
            raise ValidationError(
                "OTP has expired. Please request a new one."
            )

        if challenge.attempts >= challenge.max_attempts:
            challenge.is_used = True
            challenge.save(update_fields=["is_used"])
            raise ValidationError(
                "OTP verification limit reached. "
                "Please request a new one."
            )

        submitted_hash = hash_otp(otp)

        if challenge.code_hash != submitted_hash:
            challenge.attempts += 1
            challenge.save(update_fields=["attempts"])

            SecurityEvent.objects.create(
                user=None,
                event_type="otp_failed",
                description=(
                    f"OTP failed for "
                    f"{challenge.phone_number}"
                ),
                ip_address=request_ip,
            )

            raise ValidationError("Invalid OTP.")

        challenge.is_used = True
        challenge.verified_at = timezone.now()

        challenge.save(
            update_fields=[
                "is_used",
                "verified_at",
            ]
        )

        SecurityEvent.objects.create(
            user=None,
            event_type="otp_verified",
            description=(
                f"OTP verified for "
                f"{challenge.phone_number}"
            ),
            ip_address=request_ip,
        )

        flow_token = signing.dumps(
            {
                "challenge_id": str(challenge.id),
                "phone_number": challenge.phone_number,
                "purpose": challenge.purpose,
                "exp": int(
                    (
                            timezone.now()
                            + timedelta(minutes=10)
                    ).timestamp()
                ),
            },
            salt="auth-flow-token",
            compress=True,
        )

        return {
            "flow_token": flow_token,
            "next_step": "password",
            "expires_in": 600,
        }

    @staticmethod
    def validate_flow_token(flow_token, expected_purpose=None):
        try:
            payload = signing.loads(
                flow_token,
                salt="auth-flow-token",
                max_age=600,
            )
        except (
                signing.BadSignature,
                signing.SignatureExpired,
        ):
            raise AuthenticationFailed(
                "Invalid or expired flow token."
            )

        challenge_id = payload.get("challenge_id")

        try:
            challenge_id = int(challenge_id)
        except (TypeError, ValueError):
            raise AuthenticationFailed(
                "Invalid flow token."
            )

        challenge = (
            OTPVerification.objects
            .filter(id=challenge_id)
            .first()
        )

        if not challenge:
            raise AuthenticationFailed(
                "Invalid flow token."
            )

        if (
                expected_purpose
                and challenge.purpose != expected_purpose
        ):
            raise AuthenticationFailed(
                "Flow validation failed."
            )

        if (
                not challenge.is_used
                or not challenge.verified_at
        ):
            raise AuthenticationFailed(
                "OTP validation is required before proceeding."
            )

        return challenge, payload

    @staticmethod
    def verify_login_password(
            flow_token,
            password,
            request_ip=None,
            user_agent="",
    ):
        challenge, _ = AuthService.validate_flow_token(
            flow_token,
            expected_purpose="login",
        )

        user = (
            User.objects
            .filter(
                phone_number=challenge.phone_number
            )
            .first()
        )

        if not user or not user.is_active:
            LoginHistory.objects.create(
                user=user,
                ip_address=request_ip,
                user_agent=user_agent[:500],
                success=False,
            )

            raise AuthenticationFailed(
                "Invalid credentials."
            )

        cache_key = (
            f"login-failures:{user.phone_number}"
        )

        failed_attempts = cache.get(
            cache_key,
            0,
        )

        if failed_attempts >= 5:
            raise AuthenticationFailed(
                "Too many failed login attempts. Please try later."
            )

        if not user.check_password(password):
            cache.set(
                cache_key,
                failed_attempts + 1,
                timeout=300,
            )

            LoginHistory.objects.create(
                user=user,
                ip_address=request_ip,
                user_agent=user_agent[:500],
                success=False,
            )

            SecurityEvent.objects.create(
                user=user,
                event_type="login_failure",
                description=(
                    "Failed login with "
                    "password verification."
                ),
                ip_address=request_ip,
            )

            raise AuthenticationFailed(
                "Invalid credentials."
            )

        cache.delete(cache_key)

        refresh = RefreshToken.for_user(user)

        LoginHistory.objects.create(
            user=user,
            ip_address=request_ip,
            user_agent=user_agent[:500],
            success=True,
        )

        SecurityEvent.objects.create(
            user=user,
            event_type="login_success",
            description=(
                "Successful login via OTP and password."
            ),
            ip_address=request_ip,
        )

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "full_name": user.full_name,
                "avatar": (
                    user.avatar.url
                    if user.avatar
                    else None
                ),
                "is_phone_verified":
                    user.is_phone_verified,
                "kyc_status": user.kyc_status,
                "kyc_level": user.kyc_level,
                "created_at": (
                    user.created_at.isoformat()
                    if user.created_at
                    else None
                ),
            },
        }

    @staticmethod
    @transaction.atomic
    def register_with_password(
            flow_token,
            password,
            confirm_password,
            request_ip=None,
            user_agent="",
    ):
        challenge, _ = AuthService.validate_flow_token(
            flow_token,
            expected_purpose="registration",
        )

        if password != confirm_password:
            raise ValidationError(
                "Passwords do not match."
            )

        from django.contrib.auth.password_validation import (
            validate_password,
        )

        validate_password(password)

        if User.objects.filter(
                phone_number=challenge.phone_number
        ).exists():
            raise ValidationError(
                "This phone number is already registered."
            )

        user = User.objects.create(
            phone_number=challenge.phone_number,
            full_name="",
            is_phone_verified=True,
            phone_verified_at=timezone.now(),
        )

        user.set_password(password)

        user.save(
            update_fields=[
                "password",
                "is_phone_verified",
                "phone_verified_at",
                "updated_at",
            ]
        )

        refresh = RefreshToken.for_user(user)

        SecurityEvent.objects.create(
            user=user,
            event_type="registration_success",
            description=(
                "User registered successfully "
                "via OTP and password."
            ),
            ip_address=request_ip,
        )

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "full_name": user.full_name,
                "avatar": (
                    user.avatar.url
                    if user.avatar
                    else None
                ),
                "is_phone_verified":
                    user.is_phone_verified,
                "kyc_status": user.kyc_status,
                "kyc_level": user.kyc_level,
                "created_at": (
                    user.created_at.isoformat()
                    if user.created_at
                    else None
                ),
            },
        }
