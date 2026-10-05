from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    referenceNumber = serializers.CharField(
        source="reference_number",
        read_only=True,
    )

    type = serializers.CharField(
        source="transaction_type",
        read_only=True,
    )

    status = serializers.CharField(
        read_only=True,
    )

    assetSymbol = serializers.CharField(
        source="asset.symbol",
        read_only=True,
    )

    amount = serializers.DecimalField(
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )

    tomanAmount = serializers.DecimalField(
        source="toman_amount",
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )

    fee = serializers.DecimalField(
        max_digits=24,
        decimal_places=8,
        read_only=True,
    )

    networkCode = serializers.CharField(
        source="network_code",
        read_only=True,
    )

    address = serializers.CharField(
        read_only=True,
    )

    txId = serializers.CharField(
        source="txid",
        read_only=True,
    )

    confirmations = serializers.IntegerField(
        read_only=True,
    )

    requiredConfirmations = serializers.IntegerField(
        source="required_confirmations",
        read_only=True,
    )

    bankAccountId = serializers.CharField(
        source="bank_account_id",
        read_only=True,
    )

    orderId = serializers.CharField(
        source="order_id",
        read_only=True,
    )

    title = serializers.CharField(
        read_only=True,
    )

    description = serializers.CharField(
        read_only=True,
    )

    createdAt = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    completedAt = serializers.DateTimeField(
        source="completed_at",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Transaction

        fields = [
            "id",
            "referenceNumber",
            "type",
            "status",
            "assetSymbol",
            "amount",
            "tomanAmount",
            "fee",
            "networkCode",
            "address",
            "txId",
            "confirmations",
            "requiredConfirmations",
            "bankAccountId",
            "orderId",
            "title",
            "description",
            "createdAt",
            "completedAt",
        ]

        read_only_fields = fields