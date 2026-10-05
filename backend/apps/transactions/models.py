import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Q

from apps.accounts.models import User
from apps.assets.models import Asset


class Transaction(models.Model):
    TYPE_CHOICES = [
        ("buy", "Buy"),
        ("sell", "Sell"),
        ("toman_deposit", "Toman Deposit"),
        ("toman_withdrawal", "Toman Withdrawal"),
        ("crypto_deposit", "Crypto Deposit"),
        ("crypto_withdrawal", "Crypto Withdrawal"),
        ("fee", "Fee"),
        ("refund", "Refund"),
        ("reversal", "Reversal"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("reversed", "Reversed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    reference_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )

    amount = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        default=Decimal("0"),
    )

    toman_amount = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        default=Decimal("0"),
    )

    fee = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        default=Decimal("0"),
    )

    network_code = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    txid = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    confirmations = models.PositiveSmallIntegerField(
        default=0,
    )

    required_confirmations = models.PositiveSmallIntegerField(
        default=1,
    )

    bank_account_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    order_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )

    # Used for safe retry handling of client requests,
    # especially withdrawals.
    idempotency_key = models.CharField(
        max_length=128,
        blank=True,
        default="",
    )

    title = models.CharField(
        max_length=255,
        default="",
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="pending",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                condition=~Q(idempotency_key=""),
                name="unique_transaction_user_idempotency_key",
            ),
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name="transaction_amount_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(toman_amount__gte=0),
                name="transaction_toman_amount_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(fee__gte=0),
                name="transaction_fee_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(confirmations__gte=0),
                name="transaction_confirmations_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(required_confirmations__gte=0),
                name="transaction_required_confirmations_gte_zero",
            ),
        ]

        indexes = [
            models.Index(
                fields=["user", "status"],
                name="txn_user_status_idx",
            ),
            models.Index(
                fields=["user", "transaction_type"],
                name="txn_user_type_idx",
            ),
            models.Index(
                fields=["user", "created_at"],
                name="txn_user_created_idx",
            ),
            models.Index(
                fields=["txid"],
                name="txn_txid_idx",
            ),
            models.Index(
                fields=["order_id"],
                name="txn_order_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = (
                f"TX-{uuid.uuid4().hex[:20].upper()}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.user.phone_number} "
            f"{self.transaction_type} "
            f"{self.amount} "
            f"{self.asset.symbol}"
        )