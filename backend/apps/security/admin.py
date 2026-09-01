from django.contrib import admin

from .models import LoginHistory, SecurityEvent


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "ip_address", "created_at")
    list_filter = ("event_type",)
    search_fields = ("user__email", "description")


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "success", "created_at")
    list_filter = ("success",)
    search_fields = ("user__email", "ip_address")
