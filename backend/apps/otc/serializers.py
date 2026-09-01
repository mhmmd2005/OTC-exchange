from rest_framework import serializers

from .models import OTCDeal, OTCQuote


class OTCQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTCQuote
        fields = [
            "id",
            "user",
            "asset",
            "side",
            "requested_amount",
            "quoted_price",
            "quoted_total",
            "status",
            "expires_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OTCDealSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTCDeal
        fields = ["id", "quote", "user", "created_at"]
        read_only_fields = ["id", "created_at"]
