import hashlib
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import EmailVerification, User


class EmailVerificationService:
    TOKEN_SALT = "email-verification-token"
    TTL_SECONDS = 30 * 60
    CACHE_PREFIX = "email-verification-token:"

    @classmethod
    @transaction.atomic
    def request_verification(cls, user, email):
        email = email.strip().lower()

        if (
                user.email == email
                and user.email_verified_at
        ):
            return False

        if User.objects.filter(
                email__iexact=email,
        ).exclude(
            pk=user.pk,
        ).exists():
            raise ValidationError(
                "این ایمیل قبلاً توسط کاربر دیگری استفاده شده است."
            )

        now = timezone.now()

        EmailVerification.objects.filter(
            user=user,
            used_at__isnull=True,
        ).update(
            used_at=now,
        )

        token = signing.dumps(
            {
                "user_id": user.id,
                "email": email,
                "created_at": int(now.timestamp()),
            },
            salt=cls.TOKEN_SALT,
            compress=True,
        )

        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        verification = EmailVerification.objects.create(
            user=user,
            email=email,
            token_hash=token_hash,
            expires_at=now + timedelta(
                seconds=cls.TTL_SECONDS
            ),
        )

        user.pending_email = email
        user.save(
            update_fields=[
                "pending_email",
                "updated_at",
            ]
        )

        cache.set(
            f"{cls.CACHE_PREFIX}{verification.id}",
            token,
            timeout=cls.TTL_SECONDS,
        )

        from apps.accounts.tasks import send_email_verification_task

        transaction.on_commit(
            lambda: send_email_verification_task.delay(
                verification.id
            )
        )

        return True

    @classmethod
    def send_verification_email(cls, verification):
        token = cache.get(
            f"{cls.CACHE_PREFIX}{verification.id}"
        )

        if not token:
            return False

        frontend_url = getattr(
            settings,
            "FRONTEND_URL",
            "http://localhost:5173",
        )

        verification_url = (
            f"{frontend_url}/app/email/verify"
            f"?token={quote(token, safe='')}"
        )

        send_mail(
            subject="تأیید نشانی ایمیل",
            message=(
                f"سلام {verification.user.full_name or 'کاربر عزیز'}،\n\n"
                "برای تأیید نشانی ایمیل خود روی لینک زیر کلیک کنید:\n\n"
                f"{verification_url}\n\n"
                "این لینک تا ۳۰ دقیقه معتبر است.\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[verification.email],
            fail_silently=False,
        )

        return True

    @classmethod
    @transaction.atomic
    def verify(cls, user, token):
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        verification = (
            EmailVerification.objects
            .select_related("user")
            .filter(
                token_hash=token_hash,
                used_at__isnull=True,
            )
            .first()
        )

        if verification is None:
            raise ValidationError("لینک تأیید ایمیل معتبر نیست.")

        if verification.user_id != user.id:
            raise ValidationError("این لینک متعلق به این حساب کاربری نیست.")

        now = timezone.now()

        if verification.expires_at <= now:
            raise ValidationError("لینک تأیید ایمیل منقضی شده است.")

        try:
            payload = signing.loads(
                token,
                salt=cls.TOKEN_SALT,
                max_age=cls.TTL_SECONDS,
            )
        except signing.BadSignature:
            raise ValidationError("لینک تأیید ایمیل معتبر نیست.")

        if str(payload.get("user_id")) != str(user.id):
            raise ValidationError("لینک تأیید ایمیل معتبر نیست.")

        if payload.get("email") != verification.email:
            raise ValidationError("لینک تأیید ایمیل معتبر نیست.")

        user.email = verification.email
        user.email_verified_at = now
        user.pending_email = None

        user.save(
            update_fields=[
                "email",
                "email_verified_at",
                "pending_email",
                "updated_at",
            ]
        )

        verification.used_at = now
        verification.save(update_fields=["used_at"])

        return user
