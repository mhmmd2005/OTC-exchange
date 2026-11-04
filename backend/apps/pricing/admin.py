from django.contrib import admin

from .models import (
    AssetPricingConfig,
    ManualPriceOverride,
    PriceSnapshot,
    PriceSourceStatus,
)


@admin.register(AssetPricingConfig)
class AssetPricingConfigAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "source",
        "binance_symbol",
        "buy_spread_percent",
        "sell_spread_percent",
        "enabled",
        "updated_at",
    )

    list_filter = (
        "source",
        "enabled",
    )

    search_fields = (
        "asset__symbol",
        "asset__name",
        "binance_symbol",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = ("asset",)


@admin.register(PriceSourceStatus)
class PriceSourceStatusAdmin(admin.ModelAdmin):
    list_display = (
        "source",
        "status",
        "last_attempt_at",
        "last_success_at",
        "latency_ms",
    )

    readonly_fields = (
        "source",
        "status",
        "last_attempt_at",
        "last_success_at",
        "last_source_timestamp",
        "latency_ms",
        "last_error",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PriceSnapshot)
class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "reference_price_toman",
        "buy_price_toman",
        "sell_price_toman",
        "source",
        "pricing_mode",
        "captured_at",
    )

    list_filter = (
        "source",
        "pricing_mode",
        "asset",
    )

    search_fields = (
        "asset__symbol",
    )

    list_select_related = ("asset",)

    readonly_fields = tuple(
        field.name
        for field in PriceSnapshot._meta.fields
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ManualPriceOverride)
class ManualPriceOverrideAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "base_price_toman",
        "created_by",
        "starts_at",
        "expires_at",
        "revoked_at",
    )

    list_filter = (
        "asset",
        "created_at",
    )

    search_fields = (
        "asset__symbol",
        "reason",
    )

    readonly_fields = (
        "created_by",
        "created_at",
        "revoked_at",
        "revoked_by",
        "revocation_reason",
    )

    list_select_related = (
        "asset",
        "created_by",
        "revoked_by",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return tuple(
                field.name
                for field in self.model._meta.fields
            )

        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False