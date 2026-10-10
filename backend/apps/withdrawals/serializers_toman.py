from rest_framework import serializers


class TomanWithdrawalEstimateSerializer(
    serializers.Serializer
):
    amount = serializers.DecimalField(
        max_digits=24,
        decimal_places=8,
    )

    bankAccountId = serializers.CharField(
        max_length=50,
    )


class TomanWithdrawalCreateSerializer(
    serializers.Serializer
):
    estimateToken = serializers.CharField(
        max_length=128,
    )

    estimateVersion = serializers.IntegerField(
        min_value=1,
    )