from decimal import Decimal

from django.db import models

from apps.accounts.models import User
from apps.assets.models import Asset


class Transaction(models.Model):
    TYPE_CHOICES = [("deposit", "Deposit"), ("withdrawal", "Withdrawal"), ("transfer", "Transfer")]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="transactions")
    transaction_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    fee = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    network = models.CharField(max_length=64, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    txid = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"]), models.Index(fields=["txid"]) ]

    def __str__(self):
        return f"{self.user.email} {self.transaction_type} {self.amount} {self.asset.symbol}"
