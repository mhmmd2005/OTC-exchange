from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class PaymentAttempt(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("redirect_ready", "Redirect Ready"),
        ("callback_received", "Callback Received"),
        ("verifying", "Verifying"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    GATEWAY_CHOICES = [
        ("", "Unknown"),
        ("nexpal", "NexPal"),
        ("zarinpal", "Zarinpal"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payment_attempts",
    )

    bank_account = models.ForeignKey(
        "accounts.BankAccount",
        on_delete=models.PROTECT,
        related_name="payment_attempts",
    )

    amount = models.DecimalField(
        max_digits=24,
        decimal_places=0,
        default=0,
    )

    currency = models.CharField(
        max_length=8,
        default="IRT",
    )

    gateway = models.CharField(
        max_length=32,
        choices=GATEWAY_CHOICES,
        default="",
        blank=True,
    )

    gateway_authority = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )

    gateway_reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )

    gateway_token = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
    )

    invoice_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
    )

    gateway_code = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    gateway_message = models.TextField(
        blank=True,
        default="",
    )

    payment_url = models.URLField(
        blank=True,
        default="",
    )

    idempotency_key = models.CharField(
        max_length=128,
        unique=True,
    )

    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default="created",
        db_index=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    callback_received_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    transaction = models.OneToOneField(
        "transactions.Transaction",
        on_delete=models.PROTECT,
        related_name="payment_attempt",
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

        indexes = [
            models.Index(
                fields=["user", "status"],
            ),
            models.Index(
                fields=["gateway", "gateway_authority"],
            ),
            models.Index(
                fields=["gateway", "gateway_reference"],
            ),
            models.Index(
                fields=["created_at"],
            ),
            models.Index(
                fields=["invoice_id"],
            ),
        ]

    def __str__(self):
        return (
            f"{self.user} - "
            f"{self.amount} {self.currency} - "
            f"{self.status}"
        )