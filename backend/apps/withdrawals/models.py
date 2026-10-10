from django.db import models

from decimal import Decimal

from django.conf import settings
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




class TomanWithdrawalAttempt(models.Model):
    class Status(models.TextChoices):
        ESTIMATED = "estimated", "Estimated"
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="toman_withdrawal_attempts",
    )

    bank_account = models.ForeignKey(
        "accounts.BankAccount",
        on_delete=models.PROTECT,
        related_name="toman_withdrawal_attempts",
    )

    amount = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        default=Decimal("0"),
    )

    fee = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        default=Decimal("0"),
    )

    receivable = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        default=Decimal("0"),
    )

    # Only a hash is persisted.
    # The raw estimate token is returned to the client.
    estimate_token_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
    )

    estimate_version = models.PositiveIntegerField(
        default=1,
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ESTIMATED,
        db_index=True,
    )

    # This is the normalized internal idempotency key.
    idempotency_key = models.CharField(
        max_length=128,
        blank=True,
        default="",
        db_index=True,
    )

    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )

    provider_code = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    provider_message = models.TextField(
        blank=True,
        default="",
    )

    transaction = models.OneToOneField(
        "transactions.Transaction",
        on_delete=models.PROTECT,
        related_name="toman_withdrawal_attempt",
        null=True,
        blank=True,
    )

    expires_at = models.DateTimeField(
        db_index=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failed_at = models.DateTimeField(
        null=True,
        blank=True,
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
                    "idempotency_key",
                ],
                condition=~models.Q(
                    idempotency_key=""
                ),
                name=(
                    "unique_user_toman_withdrawal_idempotency"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=["user", "status"],
                name="toman_wd_user_status_idx",
            ),
            models.Index(
                fields=["user", "created_at"],
                name="toman_wd_user_created_idx",
            ),
            models.Index(
                fields=["expires_at", "status"],
                name="toman_wd_exp_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.phone_number} - "
            f"Toman withdrawal - "
            f"{self.amount}"
        )