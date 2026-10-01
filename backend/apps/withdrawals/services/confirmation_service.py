from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from ..validators.base import AddressValidationError
from apps.accounts.models import OTPVerification
from apps.accounts.services.auth import AuthService
from apps.security.models import SecurityEvent
from apps.security.services import TwoFactorService
from .address_service import WithdrawalAddressService
from ..models import WithdrawalAddress


class WithdrawalAddressConfirmationService:

    @staticmethod
    @transaction.atomic
    def request_confirmation(
            address,
            user,
            request_ip=None,
            user_agent="",
    ):
        address = (
            WithdrawalAddress.objects
            .select_for_update()
            .filter(
                id=address.id,
                user=user,
            )
            .first()
        )

        if not address:
            raise ValidationError(
                "آدرس برداشت پیدا نشد."
            )

        if address.status != (
                WithdrawalAddress.Status.PENDING_CONFIRMATION
        ):
            raise ValidationError(
                "این آدرس در وضعیت قابل تأیید نیست."
            )

        result = AuthService.request_otp(
            phone_number=user.phone_number,
            purpose=(
                OTPVerification.Purpose.WITHDRAWAL_ADDRESS
            ),
            request_ip=request_ip,
            user_agent=user_agent,
        )

        challenge_id = str(
            result["challenge_id"]
        )

        address.confirmation_challenge_id = (
            challenge_id
        )

        address.confirmation_requested_at = (
            timezone.now()
        )

        address.save(
            update_fields=[
                "confirmation_challenge_id",
                "confirmation_requested_at",
                "updated_at",
            ]
        )

        SecurityEvent.objects.create(
            user=user,
            event_type="withdrawal_addr_confirm_req",
            description=(
                "کد تأیید برای افزودن آدرس برداشت ارسال شد."
            ),
            ip_address=request_ip,
            user_agent=user_agent[:500],
        )

        return {
            "challengeId": challenge_id,
            "expiresIn": result["expires_in"],
            "resendAvailableIn": (
                result["resend_available_in"]
            ),
            "destinationHint": (
                    user.phone_number[:4]
                    + "***"
                    + user.phone_number[-4:]
            ),
        }

    @staticmethod
    @transaction.atomic
    def confirm(
            address_id,
            user,
            challenge_id,
            otp,
            two_factor_code=None,
            request_ip=None,
    ):
        address = (
            WithdrawalAddress.objects
            .select_for_update()
            .filter(
                id=address_id,
                user=user,
            )
            .first()
        )

        if not address:
            raise ValidationError(
                "آدرس برداشت پیدا نشد."
            )

        if address.status != (
                WithdrawalAddress.Status.PENDING_CONFIRMATION
        ):
            raise ValidationError(
                "این آدرس در وضعیت قابل تأیید نیست."
            )
        try:
            validation = WithdrawalAddressService.validate(
                network=address.network,
                address=address.address,
            )
        except AddressValidationError as exc:
            raise ValidationError(
                f"آدرس برداشت دیگر معتبر نیست: {exc}"
            ) from exc

        if validation.normalized_address != address.normalized_address:
            raise ValidationError(
                "اطلاعات آدرس برداشت با وضعیت فعلی شبکه سازگار نیست."
            )
        challenge_id = str(
            challenge_id or ""
        ).strip()

        if (
                not challenge_id
                or challenge_id
                != address.confirmation_challenge_id
        ):
            raise ValidationError(
                "کد تأیید به این آدرس برداشت تعلق ندارد."
            )

        challenge = (
            OTPVerification.objects
            .filter(
                id=challenge_id,
                phone_number=user.phone_number,
                purpose=(
                    OTPVerification.Purpose.WITHDRAWAL_ADDRESS
                ),
                is_used=False,
            )
            .first()
        )

        if not challenge:
            raise ValidationError(
                "درخواست تأیید آدرس معتبر نیست."
            )

        if TwoFactorService.is_enabled(user):
            if not two_factor_code:
                raise ValidationError(
                    "برای افزودن آدرس جدید، کد Authenticator را وارد کنید."
                )

            TwoFactorService.verify_code(
                user=user,
                code=two_factor_code,
            )

        AuthService.verify_otp(
            challenge_id=challenge.id,
            otp=otp,
            request_ip=request_ip,
            user_agent="",
            user=user,
        )

        now = timezone.now()

        cooldown_seconds = max(
            int(
                settings.WITHDRAWAL_ADDRESS_COOLDOWN_SECONDS
            ),
            0,
        )

        cooldown_until = (
                now
                + timedelta(
            seconds=cooldown_seconds
        )
        )

        address.confirmed_at = now
        address.confirmation_challenge_id = ""
        address.revoked_at = None
        address.blocked_reason = ""

        if cooldown_seconds == 0:
            address.status = (
                WithdrawalAddress.Status.ACTIVE
            )
            address.cooldown_until = None
            address.activated_at = now
        else:
            address.status = (
                WithdrawalAddress.Status.COOLING_DOWN
            )
            address.cooldown_until = cooldown_until
            address.activated_at = None

        address.save(
            update_fields=[
                "status",
                "confirmed_at",
                "confirmation_challenge_id",
                "cooldown_until",
                "activated_at",
                "revoked_at",
                "blocked_reason",
                "updated_at",
            ]
        )

        SecurityEvent.objects.create(
            user=user,
            event_type="withdrawal_addr_confirmed",
            description=(
                "آدرس برداشت با موفقیت تأیید شد و وارد دوره امنیتی شد."
            ),
            ip_address=request_ip,
        )

        if address.status == (
                WithdrawalAddress.Status.ACTIVE
        ):
            SecurityEvent.objects.create(
                user=user,
                event_type="withdrawal_addr_activated",
                description=(
                    "آدرس برداشت فعال شد."
                ),
                ip_address=request_ip,
            )

        return address

    @staticmethod
    @transaction.atomic
    def activate_if_ready(
            address_id,
            user,
            request_ip=None,
    ):
        address = (
            WithdrawalAddress.objects
            .select_for_update()
            .filter(
                id=address_id,
                user=user,
            )
            .first()
        )

        if not address:
            return None

        if address.status != (
                WithdrawalAddress.Status.COOLING_DOWN
        ):
            return address

        if not address.cooldown_until:
            return address

        now = timezone.now()

        if address.cooldown_until > now:
            return address

        address.status = (
            WithdrawalAddress.Status.ACTIVE
        )
        address.activated_at = now

        address.save(
            update_fields=[
                "status",
                "activated_at",
                "updated_at",
            ]
        )

        SecurityEvent.objects.create(
            user=user,
            event_type="withdrawal_addr_activated",
            description=(
                "دوره امنیتی آدرس برداشت پایان یافت و آدرس فعال شد."
            ),
            ip_address=request_ip,
        )

        return address
