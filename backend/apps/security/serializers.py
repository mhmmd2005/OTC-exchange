from rest_framework import serializers

from .models import LoginHistory, SecurityEvent
from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

class SecurityEventSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()

    class Meta:
        model = SecurityEvent
        fields = [
            "id",
            "user",
            "event_type",
            "description",
            "ip_address",
            "user_agent",
            "device_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "device_name",
        ]

    def get_device_name(self, obj):
        user_agent = (obj.user_agent or "").strip()

        if not user_agent:
            return "مرورگر"

        if "Edg/" in user_agent:
            browser = "Edge"
        elif "OPR/" in user_agent:
            browser = "Opera"
        elif "SamsungBrowser/" in user_agent:
            browser = "Samsung Internet"
        elif "Firefox/" in user_agent:
            browser = "Firefox"
        elif "Chrome/" in user_agent:
            browser = "Chrome"
        elif "Safari/" in user_agent:
            browser = "Safari"
        else:
            browser = "مرورگر"

        if "Windows" in user_agent:
            operating_system = "Windows"
        elif "Linux" in user_agent:
            operating_system = "Linux"
        elif "Android" in user_agent:
            operating_system = "Android"
        elif "iPhone" in user_agent or "iPad" in user_agent:
            operating_system = "iOS"
        elif "Mac OS X" in user_agent:
            operating_system = "macOS"
        else:
            operating_system = ""

        if operating_system:
            return f"{browser} در {operating_system}"

        return browser


class LoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginHistory
        fields = [
            "id",
            "user",
            "ip_address",
            "user_agent",
            "success",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]


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


class ActiveSessionSerializer(serializers.Serializer):
    id = serializers.CharField()

    device_name = serializers.CharField()

    device_type = serializers.CharField()

    browser = serializers.CharField()

    os = serializers.CharField()

    ip_address = serializers.IPAddressField(
        allow_null=True,
        required=False,
    )

    approximate_location = serializers.CharField(
        allow_null=True,
        allow_blank=True,
        required=False,
    )

    created_at = serializers.SerializerMethodField()

    last_active_at = serializers.SerializerMethodField()

    current = serializers.BooleanField()

    def _format_timestamp(
            self,
            value,
    ):
        if value is None:
            return None

        try:
            timestamp = int(value)
        except (
                TypeError,
                ValueError,
        ):
            return None

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.get_current_timezone(),
        ).isoformat()

    def get_created_at(self, obj):
        return self._format_timestamp(
            obj.get("created_at")
        )

    def get_last_active_at(self, obj):
        return self._format_timestamp(
            obj.get("last_activity")
        )
