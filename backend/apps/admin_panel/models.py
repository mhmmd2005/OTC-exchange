import uuid

from django.contrib.auth.models import AbstractBaseUser
from django.db import models

from .managers import AdminUserManager


class AdminUser(AbstractBaseUser):
    ROLE_CHOICES = (
        ("super_admin", "مدیر ارشد"),
        ("admin", "مدیر"),
    )

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="admin",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = AdminUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-created_at"]

        verbose_name = "کاربر مدیر"
        verbose_name_plural = "کاربران مدیر"

    def __str__(self):
        return self.email


class AdminSession(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    admin = models.ForeignKey(
        AdminUser,
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    refresh_jti = models.UUIDField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    last_activity_at = models.DateTimeField(
        auto_now=True,
    )

    expires_at = models.DateTimeField()

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["admin", "revoked_at"],
            ),
            models.Index(
                fields=["expires_at"],
            ),
        ]

    @property
    def is_active_session(self):
        return self.revoked_at is None

    def __str__(self):
        return f"{self.admin.email} - {self.id}"