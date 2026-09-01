from decimal import Decimal

from django.db import models

from apps.accounts.models import User
from apps.assets.models import Asset


class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallets")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="wallets")
    balance = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    available_balance = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    locked_balance = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    deposit_address = models.CharField(max_length=255, blank=True, default="")
    network = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "asset"], name="unique_user_wallet_asset")]
        indexes = [models.Index(fields=["user", "asset"]), models.Index(fields=["asset", "network"])]

    def __str__(self):
        return f"{self.user.email} - {self.asset.symbol}"
