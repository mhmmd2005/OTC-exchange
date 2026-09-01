from django.contrib import admin

from .models import OTPVerification, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["phone_number", "full_name", "email", "is_phone_verified", "is_active", "kyc_status"]
    search_fields = ["phone_number", "full_name", "email"]
    list_filter = ["is_phone_verified", "is_active", "kyc_status"]


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ["phone_number", "purpose", "expires_at", "attempts", "is_used", "delivery_status"]
    search_fields = ["phone_number"]
    list_filter = ["purpose", "is_used", "delivery_status"]
