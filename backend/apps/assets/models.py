from django.db import models


class Asset(models.Model):
    symbol = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    decimals = models.PositiveSmallIntegerField(default=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        indexes = [models.Index(fields=["symbol"]), models.Index(fields=["is_active"])]

    def __str__(self):
        return self.symbol
