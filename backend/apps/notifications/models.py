from django.db import models

from apps.accounts.models import User


class Notification(models.Model):
    CATEGORY_CHOICES = [
        ("order", "Order"),
        ("wallet", "Wallet"),
        ("security", "Security"),
        ("system", "System"),
        ("kyc", "KYC"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="system")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    action_label = models.CharField(max_length=255, blank=True, default="")
    action_url = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "category"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.phone_number} - {self.title}"
