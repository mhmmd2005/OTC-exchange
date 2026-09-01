from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "asset", "transaction_type", "amount", "fee", "status", "txid", "created_at")
    list_filter = ("transaction_type", "status", "asset")
    search_fields = ("user__email", "txid", "address")
