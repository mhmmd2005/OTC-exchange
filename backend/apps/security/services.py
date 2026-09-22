import base64
import hashlib
import secrets
from datetime import timedelta

import pyotp

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import SecurityEvent, TwoFactorCredential


class SecurityAuditService:
    """Placeholder for future security event processing."""

    @staticmethod
    def safe_ip(ip_address):
        return ip_address or "unknown"


class TwoFactorService:
    SETUP_CACHE_PREFIX = "security:2fa:setup:"
    SETUP_TTL_SECONDS = 10 * 60
    ISSUER_NAME = "Rosha"

    @staticmethod
    def _encryption_key() -> bytes:
        return hashlib.sha256(
            settings.SECRET_KEY.encode("utf-8")
        ).digest()

    @classmethod
    def _encrypt_secret(cls, secret: str) -> str:
        key = cls._encryption_key()
        nonce = secrets.token_bytes(12)

        encrypted = AESGCM(key).encrypt(
            nonce,
            secret.encode("utf-8"),
            None,
        )

        payload = nonce + encrypted

        return base64.urlsafe_b64encode(payload).decode("ascii")

    @classmethod
    def _decrypt_secret(cls, encrypted_secret: str) -> str:
        try:
            payload = base64.urlsafe_b64decode(
                encrypted_secret.encode("ascii")
            )

            nonce = payload[:12]
            ciphertext = payload[12:]

            secret = AESGCM(cls._encryption_key()).decrypt(
                nonce,
                ciphertext,
                None,
            )

            return secret.decode("utf-8")
        except Exception as exc:
            raise ValidationError(
                "اطلاعات ورود دومرحله‌ای معتبر نیست."
            ) from exc

    @classmethod
    def _cache_key(cls, setup_token: str) -> str:
        return f"{cls.SETUP_CACHE_PREFIX}{setup_token}"

    @staticmethod
    def _normalize_code(code: str) -> str:
        translation = str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789",
        )

        return str(code).translate(translation).strip()

    @classmethod
    def is_enabled(cls, user) -> bool:
        return TwoFactorCredential.objects.filter(
            user=user,
            enabled=True,
        ).exists()

    @classmethod
    def start_setup(cls, user) -> dict:
        if cls.is_enabled(user):
            raise ValidationError(
                "ورود دومرحله‌ای برای این حساب قبلاً فعال شده است."
            )

        # اگر قبلاً setup باز بوده، یکی قبلی باطل می‌شود.
        old_setup_token = getattr(
            user,
            "_two_factor_setup_token",
            None,
        )

        if old_setup_token:
            cache.delete(cls._cache_key(old_setup_token))

        secret = pyotp.random_base32()

        account_name = (
            getattr(user, "email", None)
            or getattr(user, "phone_number", None)
            or str(user.pk)
        )

        totp = pyotp.TOTP(secret)

        otpauth_uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=cls.ISSUER_NAME,
        )

        setup_token = secrets.token_urlsafe(32)

        cache.set(
            cls._cache_key(setup_token),
            {
                "user_id": user.id,
                "secret": secret,
            },
            timeout=cls.SETUP_TTL_SECONDS,
        )

        return {
            "setup_token": setup_token,
            "secret": secret,
            "otpauth_uri": otpauth_uri,
            "enabled": False,
        }

    @classmethod
    def confirm_setup(
        cls,
        user,
        code: str,
        setup_token: str,
    ) -> bool:
        if cls.is_enabled(user):
            raise ValidationError(
                "ورود دومرحله‌ای قبلاً فعال شده است."
            )

        if not setup_token:
            raise ValidationError(
                "توکن راه‌اندازی ورود دومرحله‌ای ارسال نشده است."
            )

        setup_data = cache.get(
            cls._cache_key(setup_token)
        )

        if not setup_data:
            raise ValidationError(
                "فرایند راه‌اندازی منقضی شده است؛ دوباره شروع کنید."
            )

        if int(setup_data.get("user_id")) != user.id:
            raise ValidationError(
                "توکن راه‌اندازی معتبر نیست."
            )

        secret = setup_data.get("secret")

        if not secret:
            raise ValidationError(
                "اطلاعات راه‌اندازی معتبر نیست."
            )

        normalized_code = cls._normalize_code(code)

        if not normalized_code.isdigit() or len(normalized_code) != 6:
            raise ValidationError(
                "کد Authenticator باید ۶ رقمی باشد."
            )

        totp = pyotp.TOTP(secret)

        if not totp.verify(
            normalized_code,
            valid_window=1,
        ):
            raise ValidationError(
                "کد Authenticator صحیح نیست یا منقضی شده است."
            )

        encrypted_secret = cls._encrypt_secret(secret)

        credential, _ = TwoFactorCredential.objects.update_or_create(
            user=user,
            defaults={
                "secret_encrypted": encrypted_secret,
                "enabled": True,
                "enabled_at": timezone.now(),
            },
        )

        cache.delete(
            cls._cache_key(setup_token)
        )

        SecurityEvent.objects.create(
            user=user,
            event_type="two_factor_enabled",
            description="ورود دومرحله‌ای با Authenticator فعال شد.",
        )

        return credential.enabled

    @classmethod
    def disable(cls, user) -> None:
        credential = TwoFactorCredential.objects.filter(
            user=user,
        ).first()

        if not credential:
            return

        was_enabled = credential.enabled

        credential.enabled = False
        credential.secret_encrypted = ""
        credential.enabled_at = None
        credential.save(
            update_fields=[
                "enabled",
                "secret_encrypted",
                "enabled_at",
                "updated_at",
            ]
        )

        if was_enabled:
            SecurityEvent.objects.create(
                user=user,
                event_type="two_factor_disabled",
                description="ورود دومرحله‌ای غیرفعال شد.",
            )

    @classmethod
    def get_secret(cls, user) -> str | None:
        credential = TwoFactorCredential.objects.filter(
            user=user,
            enabled=True,
        ).first()

        if not credential or not credential.secret_encrypted:
            return None

        return cls._decrypt_secret(
            credential.secret_encrypted
        )