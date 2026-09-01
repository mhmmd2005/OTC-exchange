from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "decimals", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("symbol", "name")
    ordering = ("symbol",)
