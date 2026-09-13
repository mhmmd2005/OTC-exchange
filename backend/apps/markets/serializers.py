from rest_framework import serializers

from apps.assets.models import Asset
from .models import Market


class MarketSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="asset.symbol", read_only=True)
    nameFa = serializers.CharField(source="asset.name_fa", read_only=True)
    nameEn = serializers.CharField(source="asset.name", read_only=True)
    iconUrl = serializers.CharField(source="asset.icon_url", read_only=True)
    color = serializers.CharField(source="asset.color", read_only=True)
    buyPriceToman = serializers.DecimalField(source="asset.buy_price_toman", max_digits=30, decimal_places=2, read_only=True)
    sellPriceToman = serializers.DecimalField(source="asset.sell_price_toman", max_digits=30, decimal_places=2, read_only=True)
    change24hPercent = serializers.DecimalField(source="asset.change_24h_percent", max_digits=10, decimal_places=4, read_only=True)
    high24hToman = serializers.DecimalField(source="asset.high_24h_toman", max_digits=30, decimal_places=2, read_only=True)
    low24hToman = serializers.DecimalField(source="asset.low_24h_toman", max_digits=30, decimal_places=2, read_only=True)
    tradable = serializers.BooleanField(source="asset.tradable", read_only=True)

    class Meta:
        model = Market
        fields = [
            "symbol",
            "nameFa",
            "nameEn",
            "iconUrl",
            "color",
            "buyPriceToman",
            "sellPriceToman",
            "change24hPercent",
            "high24hToman",
            "low24hToman",
            "tradable",
            "is_active",
            "volume_24h_toman",
            "last_price_toman",
        ]