import hashlib
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from ..models import AdminSession, AdminUser


LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCK_SECONDS = 60


def _login_cache_key(email, ip_address):
    raw = f"{email.lower()}:{ip_address or 'unknown'}"
    digest = hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()

    return f"admin-login:{digest}"


def _check_login_rate_limit(email, ip_address):
    key = _login_cache_key(
        email,
        ip_address,
    )

    attempts = cache.get(key, 0)

    if attempts >= LOGIN_MAX_ATTEMPTS:
        raise ValidationError(
            "Too many login attempts. Please try again later."
        )


def _record_failed_login(email, ip_address):
    key = _login_cache_key(
        email,
        ip_address,
    )

    attempts = cache.get(key, 0)

    cache.set(
        key,
        attempts + 1,
        timeout=LOGIN_LOCK_SECONDS,
    )


def _clear_failed_logins(email, ip_address):
    cache.delete(
        _login_cache_key(
            email,
            ip_address,
        )
    )


def _build_refresh_token(admin, session):
    refresh = RefreshToken()

    refresh["admin_id"] = str(admin.id)
    refresh["account_type"] = "admin"
    refresh["session_id"] = str(session.id)

    access = refresh.access_token

    access["admin_id"] = str(admin.id)
    access["account_type"] = "admin"
    access["session_id"] = str(session.id)

    return refresh, access


def _create_session(admin, request):
    now = timezone.now()

    refresh_lifetime = api_settings.REFRESH_TOKEN_LIFETIME

    session = AdminSession.objects.create(
        admin=admin,
        expires_at=now + refresh_lifetime,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get(
            "HTTP_USER_AGENT",
            "",
        )[:1000],
    )

    refresh, access = _build_refresh_token(
        admin,
        session,
    )

    session.refresh_jti = UUID(
        str(refresh["jti"])
    )

    session.save(
        update_fields=["refresh_jti"]
    )

    return refresh, access


def _validate_refresh_token(refresh_token):
    try:
        token = RefreshToken(
            refresh_token
        )
    except Exception as exc:
        raise AuthenticationFailed(
            "Invalid admin refresh token."
        ) from exc

    if token.get("account_type") != "admin":
        raise AuthenticationFailed(
            "Invalid admin refresh token."
        )

    admin_id = token.get("admin_id")
    session_id = token.get("session_id")
    token_jti = token.get("jti")

    if not admin_id or not session_id or not token_jti:
        raise AuthenticationFailed(
            "Invalid admin refresh token."
        )

    admin = (
        AdminUser.objects
        .filter(
            id=admin_id,
            is_active=True,
        )
        .first()
    )

    if not admin:
        raise AuthenticationFailed(
            "Admin account is inactive or does not exist."
        )

    session = (
        AdminSession.objects
        .filter(
            id=session_id,
            admin=admin,
            revoked_at__isnull=True,
        )
        .first()
    )

    if not session:
        raise AuthenticationFailed(
            "Admin session is invalid."
        )

    now = timezone.now()

    if session.expires_at <= now:
        session.revoked_at = now
        session.save(update_fields=["revoked_at"])

        raise AuthenticationFailed(
            "Admin session has expired."
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
            session.save(update_fields=["revoked_at"])

            raise AuthenticationFailed(
                "Admin session has expired due to inactivity."
            )

    if (
        not session.refresh_jti
        or str(session.refresh_jti) != str(token_jti)
    ):
        raise AuthenticationFailed(
            "Admin refresh token has been revoked."
        )

    return token, admin, session


class AdminAuthService:

    @staticmethod
    @transaction.atomic
    def login(
        *,
        email,
        password,
        request,
    ):
        email = email.strip().lower()

        ip_address = request.META.get(
            "REMOTE_ADDR"
        )

        _check_login_rate_limit(
            email,
            ip_address,
        )

        admin = (
            AdminUser.objects
            .filter(
                email=email,
                is_active=True,
            )
            .first()
        )

        if not admin or not admin.check_password(
            password
        ):
            _record_failed_login(
                email,
                ip_address,
            )

            raise AuthenticationFailed(
                "Invalid admin credentials."
            )

        _clear_failed_logins(
            email,
            ip_address,
        )

        refresh, access = _create_session(
            admin,
            request,
        )

        return {
            "access": str(access),
            "refresh": str(refresh),
            "user": {
                "id": admin.id,
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role,
                "account_type": "admin",
            },
        }

    @staticmethod
    def me(admin):
        return {
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "role": admin.role,
            "account_type": "admin",
        }

    @staticmethod
    @transaction.atomic
    def refresh(refresh_token):
        token, admin, session = (
            _validate_refresh_token(
                refresh_token
            )
        )

        refresh, access = _build_refresh_token(
            admin,
            session,
        )

        session.refresh_jti = UUID(
            str(refresh["jti"])
        )

        session.last_activity_at = (
            timezone.now()
        )

        session.save(
            update_fields=[
                "refresh_jti",
                "last_activity_at",
            ]
        )

        return {
            "access": str(access),
            "refresh": str(refresh),
            "user": {
                "id": admin.id,
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role,
                "account_type": "admin",
            },
        }

    @staticmethod
    @transaction.atomic
    def logout(refresh_token):
        _, admin, session = (
            _validate_refresh_token(
                refresh_token
            )
        )

        session.revoked_at = timezone.now()

        session.save(
            update_fields=["revoked_at"]
        )

        return {
            "detail": "Admin logged out successfully."
        }