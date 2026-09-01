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
