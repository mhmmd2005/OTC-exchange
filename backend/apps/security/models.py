from django.db import models

from apps.accounts.models import User


class SecurityEvent(models.Model):
    EVENT_CHOICES = [
        ("otp_requested", "OTP requested"),
        ("otp_verified", "OTP verified"),
        ("otp_failed", "OTP failed"),
        ("login_success", "Login success"),
        ("login_failure", "Login failure"),
        ("registration_success", "Registration success"),
        ("logout", "Logout"),
        ("password_change", "Password change"),
        ("kyc_update", "KYC update"),
        ("security_alert", "Security alert"),
        ("two_factor_enabled", "Two-factor enabled"),
        ("two_factor_disabled", "Two-factor disabled"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="security_events", null=True, blank=True)
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES, default="login_success")
    description = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "event_type"])]

    def __str__(self):
        return f"{self.user or 'system'} - {self.event_type}"


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="login_history", null=True, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, default="")
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "success"])]

    def __str__(self):
        return f"{self.user or 'unknown'} login @ {self.created_at.isoformat()}"




class TwoFactorCredential(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="two_factor_credential",
    )
    secret_encrypted = models.TextField(blank=True, default="")
    enabled = models.BooleanField(default=False)
    enabled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Two-Factor Credential"
        verbose_name_plural = "Two-Factor Credentials"

    def __str__(self):
        return f"2FA - {self.user}"