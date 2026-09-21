from django.conf import settings
from django.utils import timezone
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import AdminSession, AdminUser


class AdminJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)

        if header is None:
            return None

        raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(
                raw_token,
            )
        except Exception as exc:
            raise exceptions.AuthenticationFailed(
                "توکن احراز هویت مدیر نامعتبر است."
            ) from exc

        if validated_token.get("account_type") != "admin":
            raise exceptions.AuthenticationFailed(
                "احراز هویت مدیر الزامی است."
            )

        admin_id = validated_token.get("admin_id")
        session_id = validated_token.get("session_id")

        if not admin_id or not session_id:
            raise exceptions.AuthenticationFailed(
                "نشست مدیر نامعتبر است."
            )

        admin_user = (
            AdminUser.objects
            .filter(
                id=admin_id,
                is_active=True,
            )
            .first()
        )

        if not admin_user:
            raise exceptions.AuthenticationFailed(
                "حساب مدیر غیرفعال است یا وجود ندارد."
            )

        session = (
            AdminSession.objects
            .filter(
                id=session_id,
                admin=admin_user,
                revoked_at__isnull=True,
            )
            .first()
        )

        if not session:
            raise exceptions.AuthenticationFailed(
                "نشست مدیر نامعتبر است."
            )

        now = timezone.now()

        if session.expires_at <= now:
            session.revoked_at = now
            session.save(
                update_fields=["revoked_at"],
            )

            raise exceptions.AuthenticationFailed(
                "نشست مدیر منقضی شده است."
            )

        idle_timeout = getattr(
            settings,
            "JWT_IDLE_TIMEOUT_SECONDS",
            0,
        )

        if idle_timeout:
            elapsed = (
                now - session.last_activity_at
            ).total_seconds()

            if elapsed >= idle_timeout:
                session.revoked_at = now

                session.save(
                    update_fields=["revoked_at"],
                )

                raise exceptions.AuthenticationFailed(
                    "نشست مدیر به دلیل عدم فعالیت منقضی شده است."
                )

        session.last_activity_at = now

        session.save(
            update_fields=["last_activity_at"],
        )

        return admin_user, validated_token