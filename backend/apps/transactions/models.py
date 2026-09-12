from decimal import Decimal

from django.db import models

from apps.accounts.models import User
from apps.assets.models import Asset


class Transaction(models.Model):
    TYPE_CHOICES = [
        ("buy", "Buy"),
        ("sell", "Sell"),
        ("toman_deposit", "Toman Deposit"),
        ("toman_withdrawal", "Toman Withdrawal"),
        ("crypto_deposit", "Crypto Deposit"),
        ("crypto_withdrawal", "Crypto Withdrawal"),
        ("fee", "Fee"),
        ("refund", "Refund"),
        ("reversal", "Reversal"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("reversed", "Reversed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="transactions")
    reference_number = models.CharField(max_length=50, unique=True, db_index=True)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    toman_amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    fee = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    network_code = models.CharField(max_length=64, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    txid = models.CharField(max_length=255, blank=True, default="")
    confirmations = models.PositiveSmallIntegerField(default=0)
    required_confirmations = models.PositiveSmallIntegerField(default=1)
    bank_account_id = models.CharField(max_length=50, blank=True, default="")
    order_id = models.CharField(max_length=50, blank=True, default="")
    title = models.CharField(max_length=255, default="")
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["txid"]),
            models.Index(fields=["reference_number"]),
        ]

    def __str__(self):
        return f"{self.user.phone_number} {self.transaction_type} {self.amount} {self.asset.symbol}"
