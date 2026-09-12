from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    referenceNumber = serializers.CharField(source="reference_number")
    type = serializers.CharField(source="transaction_type")
    assetSymbol = serializers.CharField(source="asset.symbol", read_only=True)
    amount = serializers.DecimalField(max_digits=24, decimal_places=8)
    tomanAmount = serializers.DecimalField(source="toman_amount", max_digits=24, decimal_places=8, required=False, allow_null=True)
    fee = serializers.DecimalField(max_digits=24, decimal_places=8, required=False, allow_null=True)
    networkCode = serializers.CharField(source="network_code", required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    txId = serializers.CharField(source="txid", required=False, allow_blank=True)
    confirmations = serializers.IntegerField(required=False)
    requiredConfirmations = serializers.IntegerField(source="required_confirmations", required=False)
    bankAccountId = serializers.CharField(source="bank_account_id", required=False, allow_blank=True)
    orderId = serializers.CharField(source="order_id", required=False, allow_blank=True)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    completedAt = serializers.DateTimeField(source="completed_at", read_only=True, required=False, allow_null=True)

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
        read_only_fields = ["id", "createdAt"]
