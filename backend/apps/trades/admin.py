from django.contrib import admin

from .models import Trade


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("user", "asset", "side", "amount", "execution_price", "fee", "total", "created_at")
    list_filter = ("side", "asset")
    search_fields = ("user__email", "asset__symbol")
