from rest_framework import serializers

from .models import OTCDeal, OTCQuote


class OTCQuoteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    side = serializers.CharField()
    assetSymbol = serializers.CharField(source="asset.symbol", read_only=True)
    inputSide = serializers.CharField(source="input_side")
    rateToman = serializers.DecimalField(source="rate_toman", max_digits=24, decimal_places=8)
    cryptoAmount = serializers.DecimalField(source="crypto_amount", max_digits=24, decimal_places=8)
    tomanAmount = serializers.DecimalField(source="toman_amount", max_digits=24, decimal_places=8)
    feeToman = serializers.DecimalField(source="fee_toman", max_digits=24, decimal_places=8)
    feePercent = serializers.DecimalField(source="fee_percent", max_digits=5, decimal_places=2)
    finalTomanAmount = serializers.DecimalField(source="final_toman_amount", max_digits=24, decimal_places=8)
    minimumToman = serializers.DecimalField(source="minimum_toman", max_digits=24, decimal_places=8)
    maximumToman = serializers.DecimalField(source="maximum_toman", max_digits=24, decimal_places=8)
    expiresAt = serializers.DateTimeField(source="expires_at", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = OTCQuote
        fields = [
            "id",
            "side",
            "assetSymbol",
            "inputSide",
            "rateToman",
            "cryptoAmount",
            "tomanAmount",
            "feeToman",
            "feePercent",
            "finalTomanAmount",
            "minimumToman",
            "maximumToman",
            "status",
            "expiresAt",
            "createdAt",
        ]
        read_only_fields = ["id", "createdAt"]


class OTCDealSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTCDeal
        fields = ["id", "quote", "user", "created_at"]
        read_only_fields = ["id", "created_at"]
