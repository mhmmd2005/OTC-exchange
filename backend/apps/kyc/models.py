from django.db import models

from apps.accounts.models import User


class KycApplication(models.Model):
    STATUS_CHOICES = [
        ("not_started", "Not started"),
        ("in_progress", "In progress"),
        ("pending_review", "Pending review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="kyc_applications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")
    level = models.CharField(max_length=20, default="basic")
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="kyc_reviews", null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.user.email} - {self.status}"
