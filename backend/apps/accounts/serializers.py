from apps.accounts.models import User
from apps.accounts.services.phone import normalize_phone_number
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "full_name", "avatar", "is_phone_verified", "kyc_status", "kyc_level",
                  "created_at"]
        read_only_fields = ["id", "created_at"]


class PhoneRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(trim_whitespace=True, max_length=20)

    def validate_phone_number(self, value):
        try:
            return normalize_phone_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class OTPVerifySerializer(serializers.Serializer):
    challenge_id = serializers.CharField()
    otp = serializers.CharField(min_length=6, max_length=6)


class LoginPasswordSerializer(serializers.Serializer):
    flow_token = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RegistrationPasswordSerializer(serializers.Serializer):
    flow_token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)


class PasswordResetSerializer(serializers.Serializer):
    flow_token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
