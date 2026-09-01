from rest_framework import serializers

from .models import KycApplication


class KycApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = KycApplication
        fields = [
            "id",
            "user",
            "status",
            "level",
            "submitted_at",
            "reviewed_at",
            "reviewed_by",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
