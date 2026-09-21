from django.contrib import admin

from .models import AdminSession, AdminUser


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "role",
        "is_active",
        "created_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "email",
        "full_name",
    )


@admin.register(AdminSession)
class AdminSessionAdmin(admin.ModelAdmin):
    list_display = (
        "admin",
        "created_at",
        "last_activity_at",
        "expires_at",
        "revoked_at",
        "ip_address",
    )

    list_filter = (
        "revoked_at",
        "created_at",
    )

    search_fields = (
        "admin__email",
        "ip_address",
    )

    readonly_fields = (
        "id",
        "admin",
        "refresh_jti",
        "created_at",
        "last_activity_at",
        "expires_at",
        "revoked_at",
        "ip_address",
        "user_agent",
    )