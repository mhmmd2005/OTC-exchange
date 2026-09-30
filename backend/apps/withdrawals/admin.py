# Register your models here.
from django.contrib import admin

from .models import WithdrawalAddress


@admin.register(WithdrawalAddress)
class WithdrawalAddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "network",
        "address",
        "status",
        "is_default",
        "created_at",
    )

    list_filter = (
        "status",
        "verification_method",
        "network",
    )

    search_fields = (
        "user__phone_number",
        "user__email",
        "address",
        "normalized_address",
        "label",
    )

    readonly_fields = (
        "normalized_address",
        "created_at",
        "updated_at",
        "confirmed_at",
        "cooldown_until",
        "activated_at",
        "last_used_at",
        "revoked_at",
    )