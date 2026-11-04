from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models
from django.utils import timezone


class AssetPricingConfig(models.Model):
    class Source(models.TextChoices):
        BINANCE = "binance", "Binance Spot"
        WALLEX = "wallex", "Wallex"

    asset = models.OneToOneField(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="pricing_config",
    )

    source = models.CharField(
        max_length=16,
        choices=Source.choices,
        default=Source.BINANCE,
    )

    binance_symbol = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="نماد معاملاتی در Binance مانند BTCUSDT",
    )

    buy_spread_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal("0.5000"),
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("25")),
        ],
    )

    sell_spread_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal("0.5000"),
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("25")),
        ],
    )

    enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset__symbol"]
        verbose_name = "تنظیم قیمت‌گذاری ارز"
        verbose_name_plural = "تنظیمات قیمت‌گذاری ارزها"

    def clean(self):
        super().clean()

        if not self.asset_id:
            return

        symbol = self.asset.symbol.upper()

        if symbol == "USDT":
            if self.source != self.Source.WALLEX:
                raise ValidationError({
                    "source": "قیمت تتر باید از Wallex دریافت شود."
                })

        elif self.source == self.Source.WALLEX:
            raise ValidationError({
                "source": "Wallex در این سیستم فقط منبع مستقیم قیمت USDT است."
            })

        if (
            self.source == self.Source.BINANCE
            and not self.binance_symbol.strip()
        ):
            raise ValidationError({
                "binance_symbol": "نماد Binance الزامی است."
            })

    def __str__(self):
        return f"{self.asset.symbol} Pricing Config"


class PriceSourceStatus(models.Model):
    class Source(models.TextChoices):
        BINANCE = "binance", "Binance"
        WALLEX = "wallex", "Wallex"

    class Status(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        HEALTHY = "healthy", "Healthy"
        DEGRADED = "degraded", "Degraded"
        UNAVAILABLE = "unavailable", "Unavailable"

    source = models.CharField(
        max_length=16,
        choices=Source.choices,
        unique=True,
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.UNKNOWN,
    )

    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_success_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_source_timestamp = models.DateTimeField(
        null=True,
        blank=True,
    )

    latency_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    last_error = models.TextField(
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "وضعیت منبع قیمت"
        verbose_name_plural = "وضعیت منابع قیمت"

    def __str__(self):
        return f"{self.source}: {self.status}"


class PriceSnapshot(models.Model):
    class PricingMode(models.TextChoices):
        AUTO = "auto", "Automatic"
        MANUAL = "manual", "Manual Override"

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="price_snapshots",
    )

    reference_price_toman = models.DecimalField(
        max_digits=30,
        decimal_places=8,
    )

    buy_price_toman = models.DecimalField(
        max_digits=30,
        decimal_places=8,
    )

    sell_price_toman = models.DecimalField(
        max_digits=30,
        decimal_places=8,
    )

    asset_price_usdt = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    usdt_toman_rate = models.DecimalField(
        max_digits=30,
        decimal_places=8,
    )

    buy_spread_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
    )

    sell_spread_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
    )

    source = models.CharField(max_length=16)

    source_symbol = models.CharField(
        max_length=32,
        blank=True,
        default="",
    )

    pricing_mode = models.CharField(
        max_length=16,
        choices=PricingMode.choices,
        default=PricingMode.AUTO,
    )

    source_timestamp = models.DateTimeField(
        null=True,
        blank=True,
    )

    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-captured_at"]
        indexes = [
            models.Index(
                fields=["asset", "-captured_at"],
                name="pricing_snapshot_asset_time_idx",
            ),
            models.Index(
                fields=["source", "-captured_at"],
                name="pricing_snapshot_source_time_idx",
            ),
        ]
        verbose_name = "تاریخچه قیمت"
        verbose_name_plural = "تاریخچه قیمت‌ها"

    def __str__(self):
        return (
            f"{self.asset.symbol} - "
            f"{self.reference_price_toman} Toman"
        )


class ManualPriceOverride(models.Model):
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="manual_price_overrides",
    )

    base_price_toman = models.DecimalField(
        max_digits=30,
        decimal_places=8,
        validators=[
            MinValueValidator(Decimal("0.00000001")),
        ],
    )

    reason = models.TextField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_price_overrides",
    )

    starts_at = models.DateTimeField(
        default=timezone.now,
    )

    expires_at = models.DateTimeField()

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_price_overrides",
    )

    revocation_reason = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["asset", "starts_at", "expires_at"],
                name="pricing_override_asset_time_idx",
            ),
        ]
        verbose_name = "قیمت پایه دستی"
        verbose_name_plural = "قیمت‌های پایه دستی"

    def clean(self):
        super().clean()

        if self.base_price_toman <= 0:
            raise ValidationError({
                "base_price_toman": "قیمت پایه باید مثبت باشد."
            })

        if self.expires_at <= self.starts_at:
            raise ValidationError({
                "expires_at": "زمان پایان باید بعد از زمان شروع باشد."
            })

        if self.asset_id and self.starts_at and self.expires_at:
            overlapping = ManualPriceOverride.objects.filter(
                asset_id=self.asset_id,
                revoked_at__isnull=True,
                starts_at__lt=self.expires_at,
                expires_at__gt=self.starts_at,
            )

            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError(
                    "برای این ارز در این بازه زمانی Override دیگری وجود دارد."
                )

    def __str__(self):
        return (
            f"{self.asset.symbol} - "
            f"{self.base_price_toman} Toman"
        )