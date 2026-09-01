from django.contrib import admin

from .models import OTCDeal, OTCQuote


@admin.register(OTCQuote)
class OTCQuoteAdmin(admin.ModelAdmin):
    list_display = ("user", "asset", "side", "requested_amount", "quoted_total", "status", "expires_at")
    list_filter = ("status", "side", "asset")
    search_fields = ("user__email", "asset__symbol")


@admin.register(OTCDeal)
class OTCDealAdmin(admin.ModelAdmin):
    list_display = ("quote", "user", "created_at")
    search_fields = ("user__email", "quote__asset__symbol")
