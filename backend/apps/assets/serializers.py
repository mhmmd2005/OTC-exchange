from rest_framework import serializers

from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["id", "symbol", "name", "is_active", "decimals", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
