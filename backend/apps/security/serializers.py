from rest_framework import serializers

from .models import LoginHistory, SecurityEvent


class SecurityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityEvent
        fields = ["id", "user", "event_type", "description", "ip_address", "created_at"]
        read_only_fields = ["id", "created_at"]


class LoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginHistory
        fields = ["id", "user", "ip_address", "user_agent", "success", "created_at"]
        read_only_fields = ["id", "created_at"]


class AntiPhishingSerializer(serializers.Serializer):
    code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=20,
        trim_whitespace=True,
    )

    def validate_code(self, value):
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if len(value) < 4:
            raise serializers.ValidationError(
                "عبارت ضد فیشینگ باید حداقل ۴ کاراکتر باشد."
            )

        return value
