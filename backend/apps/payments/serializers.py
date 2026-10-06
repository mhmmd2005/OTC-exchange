from __future__ import annotations

from rest_framework import serializers

from .models import PaymentAttempt


class TomanDepositCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=24,
        decimal_places=0,
        required=True,
    )

    bankAccountId = serializers.CharField(
        required=True,
        trim_whitespace=True,
        max_length=50,
    )


class TomanDepositResponseSerializer(
    serializers.ModelSerializer
):
    id = serializers.UUIDField(
        read_only=True,
    )

    amount = serializers.DecimalField(
        max_digits=24,
        decimal_places=0,
        read_only=True,
        coerce_to_string=True,
    )

    paymentUrl = serializers.URLField(
        source="payment_url",
        read_only=True,
        allow_blank=True,
    )

    expiresAt = serializers.DateTimeField(
        source="expires_at",
        read_only=True,
    )

    status = serializers.CharField(
        read_only=True,
    )

    createdAt = serializers.DateTimeField(
        source="created_at",
        read_only=True,
    )

    class Meta:
        model = PaymentAttempt
        fields = [
            "id",
            "amount",
            "paymentUrl",
            "expiresAt",
            "status",
            "createdAt",
        ]
        read_only_fields = fields