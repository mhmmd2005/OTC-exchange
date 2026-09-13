from rest_framework import serializers

from .models import Order, OrderTimeline


class OrderTimelineSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    status = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    occurredAt = serializers.DateTimeField(source="occurred_at", required=False, allow_null=True)
    completed = serializers.BooleanField()
    current = serializers.BooleanField()

    class Meta:
        model = OrderTimeline
        fields = [
            "id",
            "status",
            "title",
            "description",
            "occurredAt",
            "completed",
            "current",
        ]


class OrderSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    orderNumber = serializers.CharField(source="order_number")
    side = serializers.CharField()
    assetSymbol = serializers.CharField(source="asset.symbol", read_only=True)
    assetNameFa = serializers.CharField(source="asset.name_fa", read_only=True)
    cryptoAmount = serializers.DecimalField(source="amount", max_digits=24, decimal_places=8)
    tomanAmount = serializers.DecimalField(source="price", max_digits=24, decimal_places=8)
    rateToman = serializers.DecimalField(source="rate_toman", max_digits=24, decimal_places=8)
    feeToman = serializers.DecimalField(source="fee_toman", max_digits=24, decimal_places=8)
    finalTomanAmount = serializers.DecimalField(source="final_toman_amount", max_digits=24, decimal_places=8)
    status = serializers.CharField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    completedAt = serializers.DateTimeField(source="completed_at", read_only=True, required=False, allow_null=True)
    paymentSource = serializers.CharField(required=False, allow_blank=True)
    destination = serializers.CharField(required=False, allow_blank=True)
    timeline = OrderTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "orderNumber",
            "side",
            "assetSymbol",
            "assetNameFa",
            "cryptoAmount",
            "tomanAmount",
            "rateToman",
            "feeToman",
            "finalTomanAmount",
            "status",
            "createdAt",
            "updatedAt",
            "completedAt",
            "paymentSource",
            "destination",
            "timeline",
        ]
        read_only_fields = ["id", "createdAt", "updatedAt"]
