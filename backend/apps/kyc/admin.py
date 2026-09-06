from django.contrib import admin

from .models import KycApplication


@admin.register(KycApplication)
class KycApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "status", "submitted_at", "reviewed_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["user__email", "user__phone_number", "first_name", "last_name"]
    readonly_fields = ["submitted_at", "reviewed_at", "created_at", "updated_at", "reviewed_by"]
    fieldsets = (
        (
            "Personal Information",
            {"fields": ("user", "first_name", "last_name", "national_id", "birth_date", "email")},
        ),
        (
            "Documents",
            {"fields": ("identity_document", "selfie")},
        ),
        (
            "Status",
            {"fields": ("status", "rejection_reason")},
        ),
        (
            "Review",
            {"fields": ("reviewed_by", "reviewed_at", "submitted_at")},
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at")},
        ),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = KycApplication.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                if obj.status == "approved":
                    obj.approve(reviewed_by=request.user)
                elif obj.status == "rejected":
                    obj.reject(obj.rejection_reason, reviewed_by=request.user)
        super().save_model(request, obj, form, change)
