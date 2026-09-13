from django.db import models


class Asset(models.Model):
    symbol = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255)
    name_fa = models.CharField(max_length=255, default="")
    icon_url = models.URLField(blank=True, default="")
    color = models.CharField(max_length=7, default="#6366f1")
    is_active = models.BooleanField(default=True)
    decimals = models.PositiveSmallIntegerField(default=8)
    price_precision = models.PositiveSmallIntegerField(default=2)
    amount_precision = models.PositiveSmallIntegerField(default=8)
    buy_price_toman = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    sell_price_toman = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    change_24h_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    high_24h_toman = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    low_24h_toman = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    tradable = models.BooleanField(default=True)
    deposit_enabled = models.BooleanField(default=True)
    withdrawal_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        indexes = [models.Index(fields=["symbol"]), models.Index(fields=["is_active"])]

    def __str__(self):
        return self.symbol


class AssetNetwork(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("congested", "Congested"),
        ("maintenance", "Maintenance"),
        ("disabled", "Disabled"),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="networks")
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, default="")
    address_regex = models.CharField(max_length=255, blank=True, default="")
    memo_required = models.BooleanField(default=False)
    deposit_enabled = models.BooleanField(default=True)
    withdrawal_enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    confirmations = models.PositiveSmallIntegerField(default=1)
    estimated_arrival_minutes = models.PositiveSmallIntegerField(default=30)
    minimum_deposit = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    minimum_withdrawal = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    withdrawal_fee = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        indexes = [models.Index(fields=["asset", "code"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.asset.symbol} - {self.code}"
