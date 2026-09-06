from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class KycApplication(models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not started"),
        ("pending", "Pending review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="kyc_application")
    first_name = models.CharField(max_length=255, blank=True, default="")
    last_name = models.CharField(max_length=255, blank=True, default="")
    national_id = models.CharField(max_length=50, blank=True, default="", unique=False)
    birth_date = models.DateField(blank=True, null=True)
    email = models.EmailField(blank=True, default="")
    identity_document = models.FileField(upload_to="kyc/identity/%Y/%m/%d/", blank=True, null=True)
    selfie = models.FileField(upload_to="kyc/selfie/%Y/%m/%d/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="kyc_reviews", null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"]), models.Index(fields=["status"])]
        verbose_name = "KYC Application"
        verbose_name_plural = "KYC Applications"

    def __str__(self):
        return f"{self.user.phone_number} - {self.get_status_display()}"

    @property
    def can_edit(self):
        return self.status in ["not_started", "rejected"]

    @property
    def can_submit(self):
        return self.status in ["not_started", "rejected"]

    def submit(self):
        self.status = "pending"
        self.submitted_at = timezone.now()
        self.save(update_fields=["status", "submitted_at", "updated_at"])
        self.user.kyc_status = "pending_review"
        self.user.save(update_fields=["kyc_status", "updated_at"])

    def approve(self, reviewed_by=None):
        self.status = "approved"
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.save(update_fields=["status", "reviewed_at", "reviewed_by", "updated_at"])
        self.user.kyc_status = "approved"
        self.user.save(update_fields=["kyc_status", "updated_at"])

    def reject(self, reason, reviewed_by=None):
        self.status = "rejected"
        self.rejection_reason = reason
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.save(update_fields=["status", "rejection_reason", "reviewed_at", "reviewed_by", "updated_at"])
        self.user.kyc_status = "rejected"
        self.user.save(update_fields=["kyc_status", "updated_at"])
