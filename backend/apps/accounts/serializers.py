from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
)

from apps.accounts.models import BankAccount, IranianBank, User
from apps.accounts.services.email import EmailVerificationService
from apps.accounts.services.phone import normalize_phone_number
from apps.accounts.services.session import (
    delete_session,
    get_session,
    get_user_session_version,
    update_session,
)
from apps.kyc.models import KycApplication


def get_user_kyc_status(user):
    kyc = (
        KycApplication.objects
        .filter(user=user)
        .only("status")
        .first()
    )

    if not kyc:
        return "not_started"

    return kyc.status


def map_kyc_status(status):
    return {
        "not_started": "not_started",
        "in_progress": "in_progress",
        "pending": "pending_review",
        "approved": "approved",
        "rejected": "rejected",
    }.get(status, "not_started")


class UserSerializer(serializers.ModelSerializer):
    kyc_status = serializers.SerializerMethodField()

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
            "kyc_status",
        ]

    def get_kyc_status(self, obj):
        return map_kyc_status(
            get_user_kyc_status(obj),
        )


class UserProfileSerializer(serializers.ModelSerializer):
    firstName = serializers.SerializerMethodField()
    lastName = serializers.SerializerMethodField()
    fullName = serializers.CharField(source="full_name", read_only=True)
    mobile = serializers.CharField(source="phone_number", read_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    identityVerified = serializers.SerializerMethodField()
    nationalId = serializers.SerializerMethodField()
    birthDate = serializers.SerializerMethodField()

    avatarUrl = serializers.ImageField(
        source="avatar",
        required=False,
        allow_null=True,
    )

    mobileVerified = serializers.BooleanField(
        source="is_phone_verified",
        read_only=True,
    )

    emailVerified = serializers.SerializerMethodField()
    bankVerified = serializers.SerializerMethodField()

    kycStatus = serializers.SerializerMethodField()

    accountLevel = serializers.CharField(
        source="kyc_level",
        read_only=True,
    )

    joinedAt = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    lastLoginAt = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

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
            "identityVerified",
        ]

        read_only_fields = [
            "id",
            "firstName",
            "lastName",
            "fullName",
            "mobile",
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
            "identityVerified",
        ]

    def _get_kyc(self, obj):
        return getattr(obj, "kyc_application", None)

    def get_firstName(self, obj):
        kyc = self._get_kyc(obj)

        if kyc and kyc.first_name:
            return kyc.first_name

        return obj.full_name.split(" ", 1)[0] if obj.full_name else ""

    def get_lastName(self, obj):
        kyc = self._get_kyc(obj)

        if kyc and kyc.last_name:
            return kyc.last_name

        parts = obj.full_name.split(" ", 1) if obj.full_name else []
        return parts[1] if len(parts) > 1 else ""

    def get_nationalId(self, obj):
        kyc = self._get_kyc(obj)
        return kyc.national_id if kyc else ""

    def get_birthDate(self, obj):
        kyc = self._get_kyc(obj)

        if not kyc or not kyc.birth_date:
            return ""

        return kyc.birth_date.isoformat()

    def get_emailVerified(self, obj):
        return bool(obj.email_verified_at)

    def get_bankVerified(self, obj):
        return obj.bank_accounts.filter(
            status="verified",
        ).exists()

    def get_kycStatus(self, obj):
        status_map = {
            "not_started": "not_started",
            "in_progress": "in_progress",
            "pending_review": "pending",
            "approved": "verified",
            "rejected": "rejected",
        }

        return status_map.get(
            map_kyc_status(
                get_user_kyc_status(obj),
            ),
            "not_started",
        )

    def get_identityVerified(self, obj):
        kyc = self._get_kyc(obj)
        return bool(
            kyc
            and kyc.basic_info_status == "approved"
            and kyc.identity_status == "approved"
        )

    def update(self, instance, validated_data):
        if "email" in validated_data:
            new_email = validated_data.pop("email")

            EmailVerificationService.request_verification(
                instance,
                new_email,
            )

        return super().update(
            instance,
            validated_data,
        )


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
    kycStatus = serializers.SerializerMethodField()
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

    def get_kycStatus(self, obj):
        return map_kyc_status(
            get_user_kyc_status(obj["user"])
        )


class BankAccountSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    bank = IranianBankSerializer(read_only=True)
    ownerName = serializers.CharField(
        source="owner_name",
        read_only=True,
    )
    cardNumber = serializers.CharField(
        source="card_number",
        read_only=True,
    )
    iban = serializers.CharField(read_only=True)
    accountNumber = serializers.CharField(
        source="account_number",
        read_only=True,
    )
    status = serializers.CharField(read_only=True)
    preferred = serializers.BooleanField(read_only=True)
    rejectionReason = serializers.CharField(
        source="rejection_reason",
        read_only=True,
    )
    createdAt = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )
    verifiedAt = serializers.DateTimeField(
        source="verified_at",
        read_only=True,
    )
    isUsable = serializers.BooleanField(
        source="is_usable",
        read_only=True,
    )

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
            "isUsable",
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

class TwoFactorLoginSerializer(serializers.Serializer):
    two_factor_token = serializers.CharField()
    code = serializers.CharField(
        min_length=6,
        max_length=6,
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

        current_version = get_user_session_version(
            user_id
        )

        if session_version != current_version:
            delete_session(session_id)
            raise AuthenticationFailed(
                "Session has been revoked."
            )

        if not update_session(
                session_id,
                user_id,
        ):
            raise AuthenticationFailed(
                "Session has expired due to inactivity."
            )

        return super().validate(attrs)


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()
