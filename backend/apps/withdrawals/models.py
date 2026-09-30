from django.db import models

from apps.accounts.models import User
from apps.assets.models import AssetNetwork


class WithdrawalAddress(models.Model):
    class Status(models.TextChoices):
        PENDING_CONFIRMATION = (
            "pending_confirmation",
            "Pending confirmation",
        )
        COOLING_DOWN = (
            "cooling_down",
            "Cooling down",
        )
        ACTIVE = (
            "active",
            "Active",
        )
        DISABLED = (
            "disabled",
            "Disabled",
        )
        BLOCKED = (
            "blocked",
            "Blocked",
        )
        REVOKED = (
            "revoked",
            "Revoked",
        )

    class VerificationMethod(models.TextChoices):
        SECURITY_CONFIRMATION = (
            "security_confirmation",
            "Security confirmation",
        )
        OWNERSHIP_SIGNATURE = (
            "ownership_signature",
            "Ownership signature",
        )
        ADMIN_VERIFIED = (
            "admin_verified",
            "Admin verified",
        )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="withdrawal_addresses",
    )

    network = models.ForeignKey(
        AssetNetwork,
        on_delete=models.PROTECT,
        related_name="withdrawal_addresses",
    )

    address = models.CharField(
        max_length=255,
    )

    normalized_address = models.CharField(
        max_length=255,
    )

    memo = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    label = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.PENDING_CONFIRMATION,
    )

    verification_method = models.CharField(
        max_length=32,
        choices=VerificationMethod.choices,
        default=VerificationMethod.SECURITY_CONFIRMATION,
    )

    is_default = models.BooleanField(
        default=False,
    )

    confirmation_requested_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    confirmation_challenge_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cooldown_until = models.DateTimeField(
        null=True,
        blank=True,
    )

    activated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    blocked_reason = models.TextField(
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

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "network",
                    "normalized_address",
                    "memo",
                ],
                name="unique_user_network_withdrawal_address",
            ),
        ]

        indexes = [
            models.Index(
                fields=["user", "status"],
            ),
            models.Index(
                fields=["user", "network"],
            ),
            models.Index(
                fields=["network", "status"],
            ),
            models.Index(
                fields=["normalized_address"],
            ),
        ]

        verbose_name = "Withdrawal Address"
        verbose_name_plural = "Withdrawal Addresses"

    def __str__(self):
        return (
            f"{self.user.phone_number} - "
            f"{self.network.asset.symbol} - "
            f"{self.network.code} - "
            f"{self.address}"
        )

    @property
    def asset(self):
        return self.network.asset

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE
