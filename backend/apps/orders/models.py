import uuid
from decimal import Decimal

from django.db import models

from apps.accounts.models import User
from apps.assets.models import Asset


def generate_order_number():
    return uuid.uuid4().hex

class Order(models.Model):
    SIDE_CHOICES = [("buy", "Buy"), ("sell", "Sell")]
    ORDER_TYPE_CHOICES = [("market", "Market"), ("limit", "Limit")]
    STATUS_CHOICES = [
        ("pending_payment", "Pending Payment"),
        ("payment_confirmed", "Payment Confirmed"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="orders")
    side = models.CharField(max_length=20, choices=SIDE_CHOICES)
    order_type = models.CharField(max_length=12, choices=ORDER_TYPE_CHOICES, default="limit")
    order_number = models.CharField(max_length=50,unique=True,db_index=True, default=generate_order_number)
    amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    price = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    rate_toman = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    fee_toman = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    final_toman_amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_payment")
    payment_source = models.CharField(max_length=255, blank=True, default="")
    destination = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["asset", "status"]),
            models.Index(fields=["order_number"]),
        ]

    def __str__(self):
        return f"{self.user.phone_number} {self.side} {self.amount} {self.asset.symbol}"


class OrderTimeline(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="timeline")
    status = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    occurred_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"
