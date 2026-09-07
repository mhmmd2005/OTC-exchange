import time

from apps.accounts.models import User
from apps.accounts.services.phone import normalize_phone_number
from apps.accounts.services.session import (
    delete_session,
    get_session,
    get_user_session_version,
)
from django.conf import settings
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "full_name",
            "avatar",
            "is_phone_verified",
            "kyc_status",
            "kyc_level",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]


class PhoneRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        trim_whitespace=True,
        max_length=20,
    )

    def validate_phone_number(self, value):
        try:
            return normalize_phone_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                str(exc)
            ) from exc


class OTPVerifySerializer(serializers.Serializer):
    challenge_id = serializers.CharField()
    otp = serializers.CharField(
        min_length=6,
        max_length=6,
    )


class LoginPasswordSerializer(serializers.Serializer):
    flow_token = serializers.CharField()
    password = serializers.CharField(
        write_only=True
    )


class RegistrationPasswordSerializer(serializers.Serializer):
    flow_token = serializers.CharField()
    password = serializers.CharField(
        write_only=True
    )
    confirm_password = serializers.CharField(
        write_only=True
    )


class PasswordResetSerializer(serializers.Serializer):
    flow_token = serializers.CharField()
    password = serializers.CharField(
        write_only=True
    )
    confirm_password = serializers.CharField(
        write_only=True
    )


class IdleTimeoutTokenRefreshSerializer(
    TokenRefreshSerializer
):
    def validate(self, attrs):
        refresh = attrs.get("refresh")

        if not refresh:
            raise AuthenticationFailed(
                "Refresh token is required."
            )

        try:
            token = self.token_class(refresh)
        except Exception as exc:
            raise AuthenticationFailed(
                "Invalid refresh token."
            ) from exc

        session_id = token.get("session_id")

        if not session_id:
            raise AuthenticationFailed(
                "Session ID is required in refresh token."
            )

        session = get_session(session_id)

        if not session:
            raise AuthenticationFailed(
                "Session not found or expired."
            )

        user_id = token.get("user_id")

        if (
            int(session.get("user_id", 0))
            != int(user_id)
        ):
            delete_session(session_id)
            raise AuthenticationFailed(
                "Session user mismatch."
            )

        session_version = int(
            session.get("session_version", 1)
        )

        current_version = (
            get_user_session_version(
                user_id
            )
        )

        if session_version != current_version:
            delete_session(session_id)
            raise AuthenticationFailed(
                "Session has been revoked."
            )

        current_time = int(time.time())
        last_activity = int(
            session.get("last_activity", 0)
        )

        if (
            current_time - last_activity
            >= settings.JWT_IDLE_TIMEOUT_SECONDS
        ):
            delete_session(session_id)
            raise AuthenticationFailed(
                "Session has expired due to inactivity."
            )

        return super().validate(attrs)