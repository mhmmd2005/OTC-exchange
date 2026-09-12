import time

from django.conf import settings
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
)

from apps.accounts.models import BankAccount, IranianBank, User
from apps.accounts.services.phone import normalize_phone_number
from apps.accounts.services.session import (
    delete_session,
    get_session,
    get_user_session_version,
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


class UserProfileSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="full_name", required=False)
    lastName = serializers.CharField(required=False, allow_blank=True)
    fullName = serializers.CharField(source="full_name", read_only=True)
    mobile = serializers.CharField(source="phone_number", read_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    nationalId = serializers.CharField(required=False, allow_blank=True, default="")
    birthDate = serializers.CharField(required=False, allow_blank=True, default="")
    avatarUrl = serializers.ImageField(source="avatar", required=False, allow_null=True)
    mobileVerified = serializers.BooleanField(source="is_phone_verified", read_only=True)
    emailVerified = serializers.BooleanField(default=False)
    bankVerified = serializers.BooleanField(default=False)
    kycStatus = serializers.CharField(source="kyc_status", read_only=True)
    accountLevel = serializers.CharField(source="kyc_level", read_only=True)
    joinedAt = serializers.DateTimeField(source="created_at", read_only=True)
    lastLoginAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "firstName",
            "lastName",
            "fullName",
            "mobile",
            "email",
            "nationalId",
            "birthDate",
            "avatarUrl",
            "mobileVerified",
            "emailVerified",
            "bankVerified",
            "kycStatus",
            "accountLevel",
            "joinedAt",
            "lastLoginAt",
        ]
        read_only_fields = [
            "id",
            "fullName",
            "mobile",
            "mobileVerified",
            "kycStatus",
            "accountLevel",
            "joinedAt",
            "lastLoginAt",
        ]

    def update(self, instance, validated_data):
        if "firstName" in validated_data or "lastName" in validated_data:
            first_name = validated_data.pop("firstName", "")
            last_name = validated_data.pop("lastName", "")
            validated_data["full_name"] = f"{first_name} {last_name}".strip()

        validated_data.pop("nationalId", None)
        validated_data.pop("birthDate", None)
        validated_data.pop("emailVerified", None)
        validated_data.pop("bankVerified", None)

        return super().update(instance, validated_data)


class UserPreferencesSerializer(serializers.Serializer):
    language = serializers.CharField(default="fa")
    theme = serializers.CharField(default="system")
    notificationChannels = serializers.DictField(
        child=serializers.BooleanField(),
        default={"email": True, "sms": True, "push": True}
    )
    priceAlerts = serializers.BooleanField(default=True)
    securityAlerts = serializers.BooleanField(default=True)
    marketingEmails = serializers.BooleanField(default=False)


class DashboardSummarySerializer(serializers.Serializer):
    user = UserProfileSerializer(read_only=True)
    totalPortfolioToman = serializers.CharField(default="0")
    tomanBalance = serializers.CharField(default="0")
    cryptoValueToman = serializers.CharField(default="0")
    pendingOrdersCount = serializers.IntegerField(default=0)
    unreadNotificationsCount = serializers.IntegerField(default=0)
    kycStatus = serializers.CharField(source="user.kyc_status", read_only=True)
    accountLevel = serializers.CharField(source="user.kyc_level", read_only=True)


class IranianBankSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    nameFa = serializers.CharField(source="name_fa")
    nameEn = serializers.CharField(source="name_en")
    cardPrefixes = serializers.JSONField(source="card_prefixes")
    color = serializers.CharField()
    logoUrl = serializers.URLField(source="logo_url", required=False, allow_blank=True)

    class Meta:
        model = IranianBank
        fields = [
            "id",
            "nameFa",
            "nameEn",
            "cardPrefixes",
            "color",
            "logoUrl",
        ]


class BankAccountSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    bank = IranianBankSerializer(read_only=True)
    ownerName = serializers.CharField(source="owner_name")
    cardNumber = serializers.CharField(source="card_number")
    iban = serializers.CharField()
    accountNumber = serializers.CharField(source="account_number", required=False, allow_blank=True)
    status = serializers.CharField()
    preferred = serializers.BooleanField()
    rejectionReason = serializers.CharField(source="rejection_reason", required=False, allow_blank=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    verifiedAt = serializers.DateTimeField(source="verified_at", read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            "id",
            "bank",
            "ownerName",
            "cardNumber",
            "iban",
            "accountNumber",
            "status",
            "preferred",
            "rejectionReason",
            "createdAt",
            "verifiedAt",
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
