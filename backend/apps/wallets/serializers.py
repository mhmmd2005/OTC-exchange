from rest_framework import serializers

from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = [
            "id",
            "asset",
            "balance",
            "available_balance",
            "locked_balance",
            "deposit_address",
            "network",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "asset",
            "balance",
            "available_balance",
            "locked_balance",
            "deposit_address",
            "network",
            "created_at",
            "updated_at",
        ]