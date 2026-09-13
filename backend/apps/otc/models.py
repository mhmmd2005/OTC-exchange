from decimal import Decimal

from django.db import models

from apps.accounts.models import User
from apps.assets.models import Asset


class OTCQuote(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("expired", "Expired"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]
    SIDE_CHOICES = [("buy", "Buy"), ("sell", "Sell")]
    INPUT_SIDE_CHOICES = [("toman", "Toman"), ("crypto", "Crypto")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otc_quotes")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="otc_quotes")
    side = models.CharField(max_length=8, choices=SIDE_CHOICES)
    input_side = models.CharField(max_length=10, choices=INPUT_SIDE_CHOICES, default="toman")
    requested_amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    rate_toman = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    crypto_amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    toman_amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    fee_toman = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    final_toman_amount = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    minimum_toman = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    maximum_toman = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"]), models.Index(fields=["asset", "status"])]

    def __str__(self):
        return f"{self.user.phone_number} {self.side} {self.requested_amount} {self.asset.symbol}"


class OTCDeal(models.Model):
    quote = models.OneToOneField(OTCQuote, on_delete=models.CASCADE, related_name="deal")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otc_deals")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deal for {self.quote.asset.symbol}"
