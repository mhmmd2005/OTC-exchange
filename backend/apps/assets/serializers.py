from rest_framework import serializers

from .models import Asset, AssetNetwork


class AssetNetworkSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    assetSymbol = serializers.CharField(source="asset.symbol", read_only=True)
    code = serializers.CharField()
    name = serializers.CharField()
    displayName = serializers.CharField(source="display_name")
    addressRegex = serializers.CharField(source="address_regex", required=False, allow_blank=True)
    memoRequired = serializers.BooleanField(source="memo_required")
    depositEnabled = serializers.BooleanField(source="deposit_enabled")
    withdrawalEnabled = serializers.BooleanField(source="withdrawal_enabled")
    status = serializers.CharField()
    confirmations = serializers.IntegerField()
    estimatedArrivalMinutes = serializers.IntegerField(source="estimated_arrival_minutes")
    minimumDeposit = serializers.DecimalField(source="minimum_deposit", max_digits=24, decimal_places=8)
    minimumWithdrawal = serializers.DecimalField(source="minimum_withdrawal", max_digits=24, decimal_places=8)
    withdrawalFee = serializers.DecimalField(source="withdrawal_fee", max_digits=24, decimal_places=8)

    class Meta:
        model = AssetNetwork
        fields = [
            "id",
            "assetSymbol",
            "code",
            "name",
            "displayName",
            "addressRegex",
            "memoRequired",
            "depositEnabled",
            "withdrawalEnabled",
            "status",
            "confirmations",
            "estimatedArrivalMinutes",
            "minimumDeposit",
            "minimumWithdrawal",
            "withdrawalFee",
        ]


class AssetSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    symbol = serializers.CharField()
    nameFa = serializers.CharField(source="name_fa")
    nameEn = serializers.CharField(source="name")
    iconUrl = serializers.URLField(source="icon_url", required=False, allow_blank=True)
    color = serializers.CharField()
    pricePrecision = serializers.IntegerField(source="price_precision")
    amountPrecision = serializers.IntegerField(source="amount_precision")
    buyPriceToman = serializers.DecimalField(source="buy_price_toman", max_digits=24, decimal_places=8)
    sellPriceToman = serializers.DecimalField(source="sell_price_toman", max_digits=24, decimal_places=8)
    change24hPercent = serializers.DecimalField(source="change_24h_percent", max_digits=10, decimal_places=2)
    high24hToman = serializers.DecimalField(source="high_24h_toman", max_digits=24, decimal_places=8)
    low24hToman = serializers.DecimalField(source="low_24h_toman", max_digits=24, decimal_places=8)
    tradable = serializers.BooleanField()
    depositEnabled = serializers.BooleanField(source="deposit_enabled")
    withdrawalEnabled = serializers.BooleanField(source="withdrawal_enabled")
    networks = AssetNetworkSerializer(many=True, read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "symbol",
            "nameFa",
            "nameEn",
            "iconUrl",
            "color",
            "pricePrecision",
            "amountPrecision",
            "buyPriceToman",
            "sellPriceToman",
            "change24hPercent",
            "high24hToman",
            "low24hToman",
            "tradable",
            "depositEnabled",
            "withdrawalEnabled",
            "networks",
            "updatedAt",
        ]
