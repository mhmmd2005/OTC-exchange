from rest_framework import serializers

from .models import Trade


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = [
            "id",
            "user",
            "order",
            "asset",
            "side",
            "amount",
            "execution_price",
            "fee",
            "total",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
