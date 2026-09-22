from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import User


class KycApplication(models.Model):
    STATUS_CHOICES = [
        ("not_started", "شروع نشده"),
        ("in_progress", "در حال تکمیل"),
        ("pending", "در انتظار بررسی"),
        ("approved", "تأیید شده"),
        ("rejected", "رد شده"),
    ]

    STEP_STATUS_CHOICES = [
        ("not_started", "شروع نشده"),
        ("pending", "در انتظار بررسی"),
        ("approved", "تأیید شده"),
        ("rejected", "رد شده"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="kyc_application",
    )

    first_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    last_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    national_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    birth_date = models.DateField(
        blank=True,
        null=True,
    )

    email = models.EmailField(
        blank=True,
        default="",
    )

    identity_document = models.FileField(
        upload_to="kyc/identity/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    selfie = models.FileField(
        upload_to="kyc/selfie/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started",
    )

    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    reviewed_by = models.ForeignKey(
        "admin_panel.AdminUser",
        on_delete=models.SET_NULL,
        related_name="kyc_reviews",
        null=True,
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
        default="",
    )

    basic_info_status = models.CharField(
        max_length=20,
        choices=STEP_STATUS_CHOICES,
        default="not_started",
    )

    basic_info_submitted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    basic_info_reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    basic_info_reviewed_by = models.ForeignKey(
        "admin_panel.AdminUser",
        on_delete=models.SET_NULL,
        related_name="basic_info_kyc_reviews",
        null=True,
        blank=True,
    )

    basic_info_rejection_reason = models.TextField(
        blank=True,
        default="",
    )

    identity_status = models.CharField(
        max_length=20,
        choices=STEP_STATUS_CHOICES,
        default="not_started",
    )

    identity_submitted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    identity_reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    identity_reviewed_by = models.ForeignKey(
        "admin_panel.AdminUser",
        on_delete=models.SET_NULL,
        related_name="identity_kyc_reviews",
        null=True,
        blank=True,
    )

    identity_rejection_reason = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["user", "status"],
            ),
            models.Index(
                fields=["status"],
            ),
            models.Index(
                fields=["basic_info_status"],
            ),
            models.Index(
                fields=["identity_status"],
            ),
        ]

        verbose_name = "درخواست احراز هویت"
        verbose_name_plural = "درخواست‌های احراز هویت"

    def __str__(self):
        return (
            f"{self.user.phone_number} - "
            f"{self.get_status_display()}"
        )

    @property
    def can_edit_basic_info(self):
        return self.basic_info_status in {
            "not_started",
            "rejected",
        }

    @property
    def can_edit_identity(self):
        return self.identity_status in {
            "not_started",
            "rejected",
        }

    @property
    def both_identity_steps_approved(self):
        return (
                self.basic_info_status == "approved"
                and self.identity_status == "approved"
        )

    def sync_status(self):
        bank_verified = self.user.bank_accounts.filter(
            status="verified",
        ).exists()

        bank_pending = self.user.bank_accounts.filter(
            status="pending",
        ).exists()

        bank_rejected = self.user.bank_accounts.filter(
            status="rejected",
        ).exists()

        if (
                self.basic_info_status == "rejected"
                or self.identity_status == "rejected"
        ):
            self.status = "rejected"

        elif (
                self.basic_info_status == "pending"
                or self.identity_status == "pending"
        ):
            self.status = "pending"

        elif self.both_identity_steps_approved:
            if bank_verified:
                self.status = "approved"

            elif bank_pending:
                self.status = "pending"

            elif bank_rejected:
                self.status = "rejected"

            else:
                self.status = "in_progress"

        elif (
                self.basic_info_status != "not_started"
                or self.identity_status != "not_started"
        ):
            self.status = "in_progress"

        else:
            self.status = "not_started"

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

    def approve_basic_info(self, reviewer):
        if self.basic_info_status != "pending":
            raise ValidationError(
                "اطلاعات هویتی در وضعیت قابل تأیید نیست."
            )

        now = timezone.now()

        self.basic_info_status = "approved"
        self.basic_info_reviewed_at = now
        self.basic_info_reviewed_by = reviewer
        self.basic_info_rejection_reason = ""

        self.reviewed_at = now
        self.reviewed_by = reviewer
        self.rejection_reason = ""

        self.save(
            update_fields=[
                "basic_info_status",
                "basic_info_reviewed_at",
                "basic_info_reviewed_by",
                "basic_info_rejection_reason",
                "reviewed_at",
                "reviewed_by",
                "rejection_reason",
                "updated_at",
            ],
        )

        self.sync_status()

    def reject_basic_info(self, reason, reviewer):
        if self.basic_info_status != "pending":
            raise ValidationError(
                "اطلاعات هویتی در وضعیت قابل رد نیست."
            )

        now = timezone.now()

        self.basic_info_status = "rejected"
        self.basic_info_reviewed_at = now
        self.basic_info_reviewed_by = reviewer
        self.basic_info_rejection_reason = reason

        self.reviewed_at = now
        self.reviewed_by = reviewer
        self.rejection_reason = reason

        self.save(
            update_fields=[
                "basic_info_status",
                "basic_info_reviewed_at",
                "basic_info_reviewed_by",
                "basic_info_rejection_reason",
                "reviewed_at",
                "reviewed_by",
                "rejection_reason",
                "updated_at",
            ],
        )

        self.sync_status()

    def approve_identity(self, reviewer):
        if self.identity_status != "pending":
            raise ValidationError(
                "مدرک شناسایی در وضعیت قابل تأیید نیست."
            )

        now = timezone.now()

        self.identity_status = "approved"
        self.identity_reviewed_at = now
        self.identity_reviewed_by = reviewer
        self.identity_rejection_reason = ""

        self.reviewed_at = now
        self.reviewed_by = reviewer
        self.rejection_reason = ""

        self.save(
            update_fields=[
                "identity_status",
                "identity_reviewed_at",
                "identity_reviewed_by",
                "identity_rejection_reason",
                "reviewed_at",
                "reviewed_by",
                "rejection_reason",
                "updated_at",
            ],
        )

        self.sync_status()

    def reject_identity(self, reason, reviewer):
        if self.identity_status != "pending":
            raise ValidationError(
                "مدرک شناسایی در وضعیت قابل رد نیست."
            )

        now = timezone.now()

        self.identity_status = "rejected"
        self.identity_reviewed_at = now
        self.identity_reviewed_by = reviewer
        self.identity_rejection_reason = reason

        self.reviewed_at = now
        self.reviewed_by = reviewer
        self.rejection_reason = reason

        self.save(
            update_fields=[
                "identity_status",
                "identity_reviewed_at",
                "identity_reviewed_by",
                "identity_rejection_reason",
                "reviewed_at",
                "reviewed_by",
                "rejection_reason",
                "updated_at",
            ],
        )

        self.sync_status()
