import secrets
import time
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import (
    AuthenticationFailed,
    Throttled,
)
from rest_framework_simplejwt.tokens import RefreshToken

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
from apps.accounts.services.phone import (
    normalize_phone_number,
)
from apps.accounts.services.session import (
    create_session,
    invalidate_all_user_sessions,
)
from apps.accounts.tasks import send_otp_sms_task
from apps.kyc.models import KycApplication
from apps.security.models import LoginHistory, SecurityEvent
from apps.security.services import TwoFactorService


class AuthService:
    LOGIN_2FA_CACHE_PREFIX = "auth:login:2fa:"
    LOGIN_2FA_TTL_SECONDS = 5 * 60
    LOGIN_2FA_MAX_ATTEMPTS = 5

    @staticmethod
    def normalize_phone(phone_number):
        return normalize_phone_number(
            phone_number
        )

    @classmethod
    def _two_factor_cache_key(
            cls,
            token: str,
    ) -> str:
        return (
            f"{cls.LOGIN_2FA_CACHE_PREFIX}"
            f"{token}"
        )

    @classmethod
    def _create_two_factor_login_challenge(
            cls,
            user,
            challenge,
    ) -> dict:
        token = secrets.token_urlsafe(32)
        expires_at = (
            int(time.time())
            + cls.LOGIN_2FA_TTL_SECONDS
        )

        cache.set(
            cls._two_factor_cache_key(token),
            {
                "user_id": user.id,
                "challenge_id": challenge.id,
                "attempts": 0,
                "expires_at": expires_at,
            },
            timeout=cls.LOGIN_2FA_TTL_SECONDS,
        )

        return {
            "next_step": "two_factor",
            "two_factor_token": token,
            "expires_in": cls.LOGIN_2FA_TTL_SECONDS,
        }

    @staticmethod
    def request_otp(
            phone_number,
            purpose,
            request_ip=None,
            user_agent="",
    ):
        normalized_phone = normalize_phone_number(
            phone_number
        )

        ip_limit = (
            check_and_increment_ip_rate_limit(
                request_ip,
                "request",
            )
        )

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

        if (
                purpose == "login"
                and not account_exists
        ):
            return {
                "allowed": False,
                "account_exists": False,
                "next_step": "registration",
                "phone_number": normalized_phone,
            }

        if (
                purpose == "registration"
                and account_exists
        ):
            return {
                "allowed": False,
                "account_exists": True,
                "message": (
                    "This phone number already has an account."
                ),
                "next_step": "login",
                "phone_number": normalized_phone,
            }

        if (
                purpose == "password_reset"
                and not account_exists
        ):
            return {
                "allowed": False,
                "account_exists": False,
                "message": (
                    "No account was found for this phone number."
                ),
                "next_step": "password_reset",
                "phone_number": normalized_phone,
            }

        if not can_resend(
            normalized_phone,
            purpose,
        ):
            raise Throttled(
                detail=(
                    "Please wait before requesting a new OTP."
                ),
                wait=(
                    settings.OTP_RESEND_COOLDOWN_SECONDS
                ),
            )

        if (
                challenge_send_count(
                    normalized_phone,
                    purpose,
                )
                >= settings.OTP_MAX_SENDS
        ):
            raise Throttled(
                detail=(
                    "Too many OTP requests. "
                    "Please try again later."
                ),
                wait=settings.OTP_SEND_WINDOW_SECONDS,
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
            lambda: send_otp_sms_task.delay(
                challenge.id
            )
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
    def get_kyc_status(user):
        return (
            KycApplication.objects
            .filter(user=user)
            .values_list(
                "status",
                flat=True,
            )
            .first()
            or "not_started"
        )

    @staticmethod
    def verify_otp(
            challenge_id,
            otp,
            request_ip=None,
            user_agent="",
            user=None,
    ):
        try:
            challenge_id = int(
                challenge_id
            )
        except (TypeError, ValueError):
            raise ValidationError(
                "Invalid verification challenge."
            )

        if challenge_id <= 0:
            raise ValidationError(
                "Invalid verification challenge."
            )

        otp = str(otp or "").strip()

        if (
                not otp.isdigit()
                or len(otp) != 6
        ):
            raise ValidationError(
                "Invalid OTP."
            )

        rate_limit = (
            check_and_increment_ip_rate_limit(
                request_ip,
                "verify",
            )
        )

        if not rate_limit["allowed"]:
            raise Throttled(
                detail=(
                    "Too many OTP requests from this IP. "
                    "Please try again later."
                ),
                wait=rate_limit["retry_after"],
            )

        try:
            challenge = OTPVerification.objects.get(
                id=challenge_id
            )
        except OTPVerification.DoesNotExist as exc:
            raise ValidationError(
                "Invalid verification challenge."
            ) from exc

        if challenge.purpose == "phone_verification":
            if not user or not user.is_authenticated:
                raise AuthenticationFailed(
                    "Authentication is required for phone verification."
                )

            challenge_phone = normalize_phone_number(
                challenge.phone_number
            )
            user_phone = normalize_phone_number(
                user.phone_number
            )

            if challenge_phone != user_phone:
                raise AuthenticationFailed(
                    "Phone verification does not belong to this account."
                )

        if challenge.is_used:
            raise ValidationError(
                "This OTP challenge has already been used."
            )

        if is_expired(challenge):
            challenge.is_used = True

            challenge.save(
                update_fields=["is_used"]
            )

            raise ValidationError(
                "OTP has expired. Please request a new one."
            )

        if challenge.attempts >= challenge.max_attempts:
            challenge.is_used = True

            challenge.save(
                update_fields=["is_used"]
            )

            raise ValidationError(
                "OTP verification limit reached. "
                "Please request a new one."
            )

        submitted_hash = hash_otp(otp)

        if challenge.code_hash != submitted_hash:
            challenge.attempts += 1

            challenge.save(
                update_fields=["attempts"]
            )

            SecurityEvent.objects.create(
                user=(
                    user
                    if user and user.is_authenticated
                    else None
                ),
                event_type="otp_failed",
                description=(
                    f"OTP failed for "
                    f"{challenge.phone_number} "
                    f"({challenge.purpose})"
                ),
                ip_address=request_ip,
            )

            raise ValidationError(
                "Invalid OTP."
            )

        challenge.is_used = True
        challenge.verified_at = timezone.now()

        challenge.save(
            update_fields=[
                "is_used",
                "verified_at",
            ]
        )

        if challenge.purpose == "phone_verification":
            user.is_phone_verified = True
            user.phone_verified_at = timezone.now()

            user.save(
                update_fields=[
                    "is_phone_verified",
                    "phone_verified_at",
                    "updated_at",
                ]
            )

        SecurityEvent.objects.create(
            user=(
                user
                if user and user.is_authenticated
                else None
            ),
            event_type="otp_verified",
            description=(
                f"OTP verified for "
                f"{challenge.phone_number} "
                f"({challenge.purpose})"
            ),
            ip_address=request_ip,
        )

        flow_token = signing.dumps(
            {
                "challenge_id": str(
                    challenge.id
                ),
                "phone_number": (
                    challenge.phone_number
                ),
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
            "next_step": (
                "completed"
                if challenge.purpose
                == "phone_verification"
                else "password"
            ),
            "expires_in": 600,
        }

    @staticmethod
    def validate_flow_token(
            flow_token,
            expected_purpose=None,
    ):
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

        challenge_id = payload.get(
            "challenge_id"
        )

        try:
            challenge_id = int(
                challenge_id
            )
        except (TypeError, ValueError):
            raise AuthenticationFailed(
                "Invalid flow token."
            )

        challenge = (
            OTPVerification.objects
            .filter(
                id=challenge_id
            )
            .first()
        )

        if not challenge:
            raise AuthenticationFailed(
                "Invalid flow token."
            )

        if (
                expected_purpose
                and challenge.purpose
                != expected_purpose
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

    @classmethod
    def verify_login_password(
            cls,
            flow_token,
            password,
            request_ip=None,
            user_agent="",
    ):
        challenge, _ = (
            cls.validate_flow_token(
                flow_token,
                expected_purpose="login",
            )
        )

        user = User.objects.filter(
            phone_number=challenge.phone_number
        ).first()

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
            f"login-failures:"
            f"{user.phone_number}"
        )

        failed_attempts = cache.get(
            cache_key,
            0,
        )

        if failed_attempts >= 5:
            raise AuthenticationFailed(
                "Too many failed login attempts. "
                "Please try later."
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
                    "Failed login with password verification."
                ),
                ip_address=request_ip,
            )

            raise AuthenticationFailed(
                "Invalid credentials."
            )

        cache.delete(
            cache_key
        )

        if TwoFactorService.is_enabled(user):
            return cls._create_two_factor_login_challenge(
                user=user,
                challenge=challenge,
            )

        refresh = RefreshToken.for_user(
            user
        )

        session_id = create_session(
            user.id
        )

        refresh["session_id"] = session_id

        access = refresh.access_token

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
            "access": str(access),
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "full_name": user.full_name,
                "avatar": (
                    user.avatar.url
                    if user.avatar
                    else None
                ),
                "is_phone_verified": (
                    user.is_phone_verified
                ),
                "kyc_status": (
                    cls.get_kyc_status(user)
                ),
                "kyc_level": user.kyc_level,
                "created_at": (
                    user.created_at.isoformat()
                    if user.created_at
                    else None
                ),
            },
        }

    @classmethod
    def verify_login_two_factor(
            cls,
            two_factor_token,
            code,
            request_ip=None,
            user_agent="",
    ):
        two_factor_token = str(
            two_factor_token or ""
        ).strip()

        if not two_factor_token:
            raise AuthenticationFailed(
                "Two-factor verification token is required."
            )

        cache_key = cls._two_factor_cache_key(
            two_factor_token
        )

        challenge_data = cache.get(
            cache_key
        )

        if not challenge_data:
            raise AuthenticationFailed(
                "فرایند تأیید ورود دومرحله‌ای منقضی شده است."
            )

        expires_at = int(
            challenge_data.get(
                "expires_at",
                0,
            )
        )

        remaining = (
            expires_at
            - int(time.time())
        )

        if remaining <= 0:
            cache.delete(cache_key)

            raise AuthenticationFailed(
                "فرایند تأیید ورود دومرحله‌ای منقضی شده است."
            )

        try:
            user_id = int(
                challenge_data.get(
                    "user_id"
                )
            )
            challenge_id = int(
                challenge_data.get(
                    "challenge_id"
                )
            )
        except (
                TypeError,
                ValueError,
        ):
            cache.delete(cache_key)

            raise AuthenticationFailed(
                "توکن تأیید ورود معتبر نیست."
            )

        user = User.objects.filter(
            id=user_id,
            is_active=True,
        ).first()

        if not user:
            cache.delete(cache_key)

            raise AuthenticationFailed(
                "حساب کاربری معتبر نیست."
            )

        challenge = (
            OTPVerification.objects
            .filter(
                id=challenge_id,
                purpose="login",
                is_used=True,
            )
            .first()
        )

        if (
                not challenge
                or not challenge.verified_at
        ):
            cache.delete(cache_key)

            raise AuthenticationFailed(
                "فرایند ورود معتبر نیست."
            )

        if not TwoFactorService.is_enabled(
            user
        ):
            cache.delete(cache_key)

            raise AuthenticationFailed(
                "ورود دومرحله‌ای برای این حساب فعال نیست."
            )

        try:
            TwoFactorService.verify_code(
                user=user,
                code=code,
            )
        except ValidationError as exc:
            attempts = int(
                challenge_data.get(
                    "attempts",
                    0,
                )
            ) + 1

            if (
                    attempts
                    >= cls.LOGIN_2FA_MAX_ATTEMPTS
            ):
                cache.delete(
                    cache_key
                )

                raise AuthenticationFailed(
                    "تعداد تلاش‌های ورود دومرحله‌ای بیش از حد مجاز است. "
                    "لطفاً دوباره وارد شوید."
                )

            challenge_data["attempts"] = attempts

            cache.set(
                cache_key,
                challenge_data,
                timeout=remaining,
            )

            raise exc

        cache.delete(
            cache_key
        )

        refresh = RefreshToken.for_user(
            user
        )

        session_id = create_session(
            user.id
        )

        refresh["session_id"] = session_id

        access = refresh.access_token

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
                "Successful login via OTP, password, "
                "and Authenticator."
            ),
            ip_address=request_ip,
        )

        return {
            "refresh": str(refresh),
            "access": str(access),
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "full_name": user.full_name,
                "avatar": (
                    user.avatar.url
                    if user.avatar
                    else None
                ),
                "is_phone_verified": (
                    user.is_phone_verified
                ),
                "kyc_status": (
                    cls.get_kyc_status(user)
                ),
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
        challenge, _ = (
            AuthService.validate_flow_token(
                flow_token,
                expected_purpose="registration",
            )
        )

        if password != confirm_password:
            raise ValidationError(
                "Passwords do not match."
            )

        from django.contrib.auth.password_validation import (
            validate_password,
        )

        validate_password(
            password
        )

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

        user.set_password(
            password
        )

        user.save(
            update_fields=[
                "password",
                "is_phone_verified",
                "phone_verified_at",
                "updated_at",
            ]
        )

        refresh = RefreshToken.for_user(
            user
        )

        session_id = create_session(
            user.id
        )

        refresh["session_id"] = session_id

        access = refresh.access_token

        SecurityEvent.objects.create(
            user=user,
            event_type="registration_success",
            description=(
                "User registered successfully via OTP and password."
            ),
            ip_address=request_ip,
        )

        return {
            "refresh": str(refresh),
            "access": str(access),
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "full_name": user.full_name,
                "avatar": (
                    user.avatar.url
                    if user.avatar
                    else None
                ),
                "is_phone_verified": (
                    user.is_phone_verified
                ),
                "kyc_status": (
                    AuthService.get_kyc_status(
                        user
                    )
                ),
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
    def reset_password(
            flow_token,
            password,
            confirm_password,
            request_ip=None,
            user_agent="",
    ):
        challenge, _ = (
            AuthService.validate_flow_token(
                flow_token,
                expected_purpose="password_reset",
            )
        )

        if password != confirm_password:
            raise ValidationError(
                "Passwords do not match."
            )

        from django.contrib.auth.password_validation import (
            validate_password,
        )

        validate_password(
            password
        )

        user = User.objects.filter(
            phone_number=challenge.phone_number,
            is_active=True,
        ).first()

        if not user:
            raise ValidationError(
                "User account not found."
            )

        user.set_password(
            password
        )

        user.save(
            update_fields=[
                "password",
                "updated_at",
            ]
        )

        invalidate_all_user_sessions(
            user.id
        )

        SecurityEvent.objects.create(
            user=user,
            event_type="password_reset_success",
            description=(
                "Password reset successfully via OTP."
            ),
            ip_address=request_ip,
        )

        return {
            "message": "Password reset successfully.",
        }