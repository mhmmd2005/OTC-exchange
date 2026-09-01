from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "asset", "side", "order_type", "amount", "price", "status")
    list_filter = ("side", "order_type", "status", "asset")
    search_fields = ("user__email", "asset__symbol")
