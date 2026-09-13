from django.db import models
from apps.assets.models import Asset


class Market(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name="market",
    )
    is_active = models.BooleanField(default=True)
    volume_24h_toman = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        default=0,
    )
    last_price_toman = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        default=0,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset.symbol} Market"