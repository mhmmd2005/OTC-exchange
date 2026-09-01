from decimal import Decimal

from django.db import models

from apps.accounts.models import User
from apps.assets.models import Asset
from apps.orders.models import Order


class Trade(models.Model):
    SIDE_CHOICES = [("buy", "Buy"), ("sell", "Sell")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trades")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="trades")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="trades")
    side = models.CharField(max_length=8, choices=SIDE_CHOICES)
    amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    execution_price = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    fee = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    total = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"]), models.Index(fields=["asset", "created_at"])]

    def __str__(self):
        return f"{self.user.email} {self.side} {self.amount} {self.asset.symbol}"
