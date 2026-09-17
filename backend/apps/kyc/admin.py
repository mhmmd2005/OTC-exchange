from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse

from .models import KycApplication


@admin.action(description="تأیید اطلاعات هویتی")
def approve_basic_info(modeladmin, request, queryset):
    success = 0

    for kyc in queryset.select_related("user"):
        try:
            with transaction.atomic():
                kyc.approve_basic_info(request.user)
            success += 1
        except ValidationError as exc:
            modeladmin.message_user(
                request,
                f"{kyc}: {exc}",
                level=messages.ERROR,
            )

    if success:
        modeladmin.message_user(
            request,
            f"{success} مورد اطلاعات هویتی تأیید شد.",
            level=messages.SUCCESS,
        )


@admin.action(description="رد اطلاعات هویتی")
def reject_basic_info(modeladmin, request, queryset):
    success = 0
    skipped = 0

    for kyc in queryset.select_related("user"):
        reason = kyc.basic_info_rejection_reason.strip()

        if not reason:
            modeladmin.message_user(
                request,
                f"برای {kyc} ابتدا دلیل رد اطلاعات هویتی را وارد کنید.",
                level=messages.WARNING,
            )
            skipped += 1
            continue

        try:
            with transaction.atomic():
                kyc.reject_basic_info(reason, request.user)
            success += 1
        except ValidationError as exc:
            modeladmin.message_user(
                request,
                f"{kyc}: {exc}",
                level=messages.ERROR,
            )

    if success:
        modeladmin.message_user(
            request,
            f"{success} مورد اطلاعات هویتی رد شد.",
            level=messages.SUCCESS,
        )

    if skipped:
        modeladmin.message_user(
            request,
            f"{skipped} مورد به دلیل نداشتن دلیل رد انجام نشد.",
            level=messages.WARNING,
        )


@admin.action(description="تأیید مدرک شناسایی")
def approve_identity(modeladmin, request, queryset):
    success = 0

    for kyc in queryset.select_related("user"):
        try:
            with transaction.atomic():
                kyc.approve_identity(request.user)
            success += 1
        except ValidationError as exc:
            modeladmin.message_user(
                request,
                f"{kyc}: {exc}",
                level=messages.ERROR,
            )

    if success:
        modeladmin.message_user(
            request,
            f"{success} مورد مدرک شناسایی تأیید شد.",
            level=messages.SUCCESS,
        )


@admin.action(description="رد مدرک شناسایی")
def reject_identity(modeladmin, request, queryset):
    success = 0
    skipped = 0

    for kyc in queryset.select_related("user"):
        reason = kyc.identity_rejection_reason.strip()

        if not reason:
            modeladmin.message_user(
                request,
                f"برای {kyc} ابتدا دلیل رد مدرک شناسایی را وارد کنید.",
                level=messages.WARNING,
            )
            skipped += 1
            continue

        try:
            with transaction.atomic():
                kyc.reject_identity(reason, request.user)
            success += 1
        except ValidationError as exc:
            modeladmin.message_user(
                request,
                f"{kyc}: {exc}",
                level=messages.ERROR,
            )

    if success:
        modeladmin.message_user(
            request,
            f"{success} مورد مدرک شناسایی رد شد.",
            level=messages.SUCCESS,
        )

    if skipped:
        modeladmin.message_user(
            request,
            f"{skipped} مورد به دلیل نداشتن دلیل رد انجام نشد.",
            level=messages.WARNING,
        )


@admin.register(KycApplication)
class KycApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "status",
        "basic_info_status",
        "identity_status",
        "submitted_at",
        "reviewed_at",
    ]
    list_filter = [
        "status",
        "basic_info_status",
        "identity_status",
        "created_at",
    ]
    search_fields = [
        "user__email",
        "user__phone_number",
        "first_name",
        "last_name",
        "national_id",
    ]
    readonly_fields = [
        "status",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
        "basic_info_status",
        "basic_info_submitted_at",
        "basic_info_reviewed_at",
        "basic_info_reviewed_by",
        "identity_status",
        "identity_submitted_at",
        "identity_reviewed_at",
        "identity_reviewed_by",
        "created_at",
        "updated_at",
    ]
    actions = [
        approve_basic_info,
        reject_basic_info,
        approve_identity,
        reject_identity,
    ]
    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "user",
                    "first_name",
                    "last_name",
                    "national_id",
                    "birth_date",
                    "email",
                )
            },
        ),
        (
            "Identity Document",
            {
                "fields": (
                    "identity_document",
                )
            },
        ),
        (
            "Basic Information Review",
            {
                "fields": (
                    "basic_info_status",
                    "basic_info_submitted_at",
                    "basic_info_reviewed_at",
                    "basic_info_reviewed_by",
                    "basic_info_rejection_reason",
                )
            },
        ),
        (
            "Identity Document Review",
            {
                "fields": (
                    "identity_status",
                    "identity_submitted_at",
                    "identity_reviewed_at",
                    "identity_reviewed_by",
                    "identity_rejection_reason",
                )
            },
        ),
        (
            "Application Status",
            {
                "fields": (
                    "status",
                    "rejection_reason",
                    "reviewed_by",
                    "reviewed_at",
                    "submitted_at",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    class Media:
        css = {
            "all": ("admin/kyc/kyc.css",)
        }

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff and super().has_change_permission(request, obj)

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "<path:object_id>/approve-basic-info/",
                self.admin_site.admin_view(self.approve_basic_info_view),
                name="kyc_kycapplication_approve_basic_info",
            ),
            path(
                "<path:object_id>/reject-basic-info/",
                self.admin_site.admin_view(self.reject_basic_info_view),
                name="kyc_kycapplication_reject_basic_info",
            ),
            path(
                "<path:object_id>/approve-identity/",
                self.admin_site.admin_view(self.approve_identity_view),
                name="kyc_kycapplication_approve_identity",
            ),
            path(
                "<path:object_id>/reject-identity/",
                self.admin_site.admin_view(self.reject_identity_view),
                name="kyc_kycapplication_reject_identity",
            ),
        ]

        return custom_urls + urls

    def changeform_view(
            self,
            request,
            object_id=None,
            form_url="",
            extra_context=None,
    ):
        extra_context = extra_context or {}

        if object_id:
            extra_context["kyc_admin_actions"] = {
                "approve_basic_info": reverse(
                    "admin:kyc_kycapplication_approve_basic_info",
                    args=[object_id],
                ),
                "reject_basic_info": reverse(
                    "admin:kyc_kycapplication_reject_basic_info",
                    args=[object_id],
                ),
                "approve_identity": reverse(
                    "admin:kyc_kycapplication_approve_identity",
                    args=[object_id],
                ),
                "reject_identity": reverse(
                    "admin:kyc_kycapplication_reject_identity",
                    args=[object_id],
                ),
            }

        return super().changeform_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

    def approve_basic_info_view(self, request, object_id):
        if request.method != "POST":
            return HttpResponseRedirect(
                reverse(
                    "admin:kyc_kycapplication_change",
                    args=[object_id],
                )
            )

        kyc = get_object_or_404(KycApplication, pk=object_id)

        try:
            with transaction.atomic():
                kyc.approve_basic_info(request.user)

            self.message_user(
                request,
                "اطلاعات هویتی با موفقیت تأیید شد.",
                level=messages.SUCCESS,
            )
        except ValidationError as exc:
            self.message_user(
                request,
                str(exc),
                level=messages.ERROR,
            )

        return HttpResponseRedirect(
            reverse(
                "admin:kyc_kycapplication_change",
                args=[object_id],
            )
        )

    def reject_basic_info_view(self, request, object_id):
        kyc = get_object_or_404(KycApplication, pk=object_id)

        if request.method == "POST":
            reason = request.POST.get(
                "reason",
                "",
            ).strip()

            if not reason:
                self.message_user(
                    request,
                    "دلیل رد اطلاعات هویتی را وارد کنید.",
                    level=messages.ERROR,
                )
            else:
                try:
                    with transaction.atomic():
                        kyc.reject_basic_info(
                            reason,
                            request.user,
                        )

                    self.message_user(
                        request,
                        "اطلاعات هویتی با موفقیت رد شد.",
                        level=messages.WARNING,
                    )

                    return HttpResponseRedirect(
                        reverse(
                            "admin:kyc_kycapplication_change",
                            args=[object_id],
                        )
                    )
                except ValidationError as exc:
                    self.message_user(
                        request,
                        str(exc),
                        level=messages.ERROR,
                    )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "رد اطلاعات هویتی",
            "kyc": kyc,
            "action_url": reverse(
                "admin:kyc_kycapplication_reject_basic_info",
                args=[object_id],
            ),
            "cancel_url": reverse(
                "admin:kyc_kycapplication_change",
                args=[object_id],
            ),
        }

        return TemplateResponse(
            request,
            "admin/kyc/reject_step.html",
            context,
        )

    def approve_identity_view(self, request, object_id):
        if request.method != "POST":
            return HttpResponseRedirect(
                reverse(
                    "admin:kyc_kycapplication_change",
                    args=[object_id],
                )
            )

        kyc = get_object_or_404(KycApplication, pk=object_id)

        try:
            with transaction.atomic():
                kyc.approve_identity(request.user)

            self.message_user(
                request,
                "مدرک شناسایی با موفقیت تأیید شد.",
                level=messages.SUCCESS,
            )
        except ValidationError as exc:
            self.message_user(
                request,
                str(exc),
                level=messages.ERROR,
            )

        return HttpResponseRedirect(
            reverse(
                "admin:kyc_kycapplication_change",
                args=[object_id],
            )
        )

    def reject_identity_view(self, request, object_id):
        kyc = get_object_or_404(KycApplication, pk=object_id)

        if request.method == "POST":
            reason = request.POST.get(
                "reason",
                "",
            ).strip()

            if not reason:
                self.message_user(
                    request,
                    "دلیل رد مدرک شناسایی را وارد کنید.",
                    level=messages.ERROR,
                )
            else:
                try:
                    with transaction.atomic():
                        kyc.reject_identity(
                            reason,
                            request.user,
                        )

                    self.message_user(
                        request,
                        "مدرک شناسایی با موفقیت رد شد.",
                        level=messages.WARNING,
                    )

                    return HttpResponseRedirect(
                        reverse(
                            "admin:kyc_kycapplication_change",
                            args=[object_id],
                        )
                    )
                except ValidationError as exc:
                    self.message_user(
                        request,
                        str(exc),
                        level=messages.ERROR,
                    )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "رد مدرک شناسایی",
            "kyc": kyc,
            "action_url": reverse(
                "admin:kyc_kycapplication_reject_identity",
                args=[object_id],
            ),
            "cancel_url": reverse(
                "admin:kyc_kycapplication_change",
                args=[object_id],
            ),
        }

        return TemplateResponse(
            request,
            "admin/kyc/reject_step.html",
            context,
        )
