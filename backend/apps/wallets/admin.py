from django.contrib import admin

from .models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "asset", "balance", "available_balance", "locked_balance", "network")
    list_filter = ("asset", "network")
    search_fields = ("user__email", "asset__symbol", "deposit_address")
