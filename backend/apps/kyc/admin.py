from django.contrib import admin

from .models import KycApplication


@admin.register(KycApplication)
class KycApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "level", "submitted_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "level")
    search_fields = ("user__email", "rejection_reason")
