from rest_framework import serializers

from .models import Asset, AssetNetwork


class AssetNetworkSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    assetSymbol = serializers.CharField(
        source="asset.symbol",
        read_only=True,
    )
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    displayName = serializers.CharField(
        source="display_name",
        read_only=True,
    )
    addressRegex = serializers.CharField(
        source="address_regex",
        read_only=True,
    )
    memoRequired = serializers.BooleanField(
        source="memo_required",
        read_only=True,
    )
    depositEnabled = serializers.BooleanField(
        source="deposit_enabled",
        read_only=True,
    )
    withdrawalEnabled = serializers.BooleanField(
        source="withdrawal_enabled",
        read_only=True,
    )
    status = serializers.CharField(read_only=True)
    confirmations = serializers.IntegerField(
        read_only=True,
    )
    estimatedArrivalMinutes = serializers.IntegerField(
        source="estimated_arrival_minutes",
        read_only=True,
    )
    minimumDeposit = serializers.DecimalField(
        source="minimum_deposit",
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )
    minimumWithdrawal = serializers.DecimalField(
        source="minimum_withdrawal",
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )
    withdrawalFee = serializers.DecimalField(
        source="withdrawal_fee",
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )

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

    symbol = serializers.CharField(read_only=True)
    nameFa = serializers.CharField(
        source="name_fa",
        read_only=True,
    )
    nameEn = serializers.CharField(
        source="name",
        read_only=True,
    )
    iconUrl = serializers.URLField(
        source="icon_url",
        read_only=True,
    )
    color = serializers.CharField(read_only=True)

    pricePrecision = serializers.IntegerField(
        source="price_precision",
        read_only=True,
    )
    amountPrecision = serializers.IntegerField(
        source="amount_precision",
        read_only=True,
    )

    buyPriceToman = serializers.DecimalField(
        source="buy_price_toman",
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )
    sellPriceToman = serializers.DecimalField(
        source="sell_price_toman",
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )
    change24hPercent = serializers.DecimalField(
        source="change_24h_percent",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    high24hToman = serializers.DecimalField(
        source="high_24h_toman",
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )
    low24hToman = serializers.DecimalField(
        source="low_24h_toman",
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )

    tradable = serializers.BooleanField(read_only=True)

    depositEnabled = serializers.BooleanField(
        source="deposit_enabled",
        read_only=True,
    )
    withdrawalEnabled = serializers.BooleanField(
        source="withdrawal_enabled",
        read_only=True,
    )

    networks = AssetNetworkSerializer(
        many=True,
        read_only=True,
    )

    updatedAt = serializers.DateTimeField(
        source="updated_at",
        read_only=True,
    )

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