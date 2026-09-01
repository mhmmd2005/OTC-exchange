from decimal import Decimal

from django.db import models

from apps.accounts.models import User
from apps.assets.models import Asset


class Order(models.Model):
    SIDE_CHOICES = [("buy", "Buy"), ("sell", "Sell")]
    ORDER_TYPE_CHOICES = [("market", "Market"), ("limit", "Limit")]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("open", "Open"),
        ("partially_filled", "Partially filled"),
        ("filled", "Filled"),
        ("cancelled", "Cancelled"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="orders")
    side = models.CharField(max_length=8, choices=SIDE_CHOICES)
    order_type = models.CharField(max_length=12, choices=ORDER_TYPE_CHOICES, default="limit")
    amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    price = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"]), models.Index(fields=["asset", "status"])]

    def __str__(self):
        return f"{self.user.email} {self.side} {self.amount} {self.asset.symbol}"
