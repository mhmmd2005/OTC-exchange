from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.services.phone import normalize_phone_number


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The phone_number field must be set.")
        normalized_phone = normalize_phone_number(phone_number)
        user = self.model(phone_number=normalized_phone, **extra_fields)
        if password is not None:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(blank=True, null=True, unique=True, default=None)

    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    full_name = models.CharField(max_length=255, blank=True, default="")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    pending_email = models.EmailField(
        blank=True,
        null=True,
    )
    kyc_level = models.CharField(max_length=20, default="basic")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    anti_phishing_code = models.CharField(max_length=20, blank=True, default="")
    withdrawal_whitelist_enabled = models.BooleanField(default=False)
    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["phone_number"]),
        ]

    def __str__(self):
        return self.phone_number


class EmailVerification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verifications",
    )
    email = models.EmailField()
    token_hash = models.CharField(
        max_length=64,
        unique=True,
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "created_at"]
            ),
            models.Index(
                fields=["expires_at"]
            ),
        ]


class OTPVerification(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        REGISTRATION = "registration", "Registration"
        PASSWORD_RESET = "password_reset", "Password Reset"
        PHONE_VERIFICATION = "phone_verification", "Phone Verification"
        WITHDRAWAL_ADDRESS = "withdrawal_address", "Withdrawal Address"

    class DeliveryStatus(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    phone_number = models.CharField(max_length=20, db_index=True)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    code_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    is_used = models.BooleanField(default=False)
    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.QUEUED,
    )
    last_sent_at = models.DateTimeField(null=True, blank=True)
    request_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone_number", "purpose", "created_at"]),
            models.Index(fields=["phone_number", "purpose", "is_used"]),
        ]

    def __str__(self):
        return f"{self.phone_number} ({self.purpose})"


class IranianBank(models.Model):
    name_fa = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255)
    sheba_code = models.CharField(
        max_length=3,
        blank=True,
        default="",
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )
    card_prefixes = models.JSONField(default=list)
    color = models.CharField(max_length=7, default="#6366f1")
    logo_url = models.URLField(blank=True, default="")

    class Meta:
        ordering = ["name_fa"]

    def __str__(self):
        return self.name_fa


class BankCardPrefix(models.Model):
    bank = models.ForeignKey(
        IranianBank,
        on_delete=models.CASCADE,
        related_name="bank_card_prefixes",
    )
    prefix = models.CharField(max_length=16, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_legacy = models.BooleanField(default=False, db_index=True)
    source = models.CharField(max_length=50, default="manual", db_index=True)
    source_url = models.URLField(blank=True, default="")
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-prefix"]
        unique_together = ("bank", "prefix")
        indexes = [
            models.Index(fields=["bank", "prefix", "is_active"]),
            models.Index(fields=["bank", "is_active", "is_legacy"]),
        ]

    def __str__(self):
        return f"{self.bank.name_fa} - {self.prefix}"


class BankVerificationObservation(models.Model):
    RESULT_INVALID_CARD = "invalid_card"
    RESULT_INVALID_IBAN = "invalid_iban"
    RESULT_DUPLICATE_CARD = "duplicate_card"
    RESULT_DUPLICATE_IBAN = "duplicate_iban"
    RESULT_UNKNOWN_CARD_PREFIX = "unknown_card_prefix"
    RESULT_UNKNOWN_IBAN_BANK = "unknown_iban_bank"
    RESULT_BANK_MISMATCH = "bank_mismatch"
    RESULT_OWNERSHIP_FAILED = "ownership_failed"
    RESULT_OWNERSHIP_UNAVAILABLE = "ownership_unavailable"
    RESULT_VERIFIED = "verified"
    RESULT_CHOICES = [
        (RESULT_INVALID_CARD, "Invalid Card"),
        (RESULT_INVALID_IBAN, "Invalid IBAN"),
        (RESULT_DUPLICATE_CARD, "Duplicate Card"),
        (RESULT_DUPLICATE_IBAN, "Duplicate IBAN"),
        (RESULT_UNKNOWN_CARD_PREFIX, "Unknown Card Prefix"),
        (RESULT_UNKNOWN_IBAN_BANK, "Unknown IBAN Bank"),
        (RESULT_BANK_MISMATCH, "Bank Mismatch"),
        (RESULT_OWNERSHIP_FAILED, "Ownership Failed"),
        (RESULT_OWNERSHIP_UNAVAILABLE, "Ownership Unavailable"),
        (RESULT_VERIFIED, "Verified"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bank_verification_observations",
    )
    card_prefix = models.CharField(max_length=16, blank=True, default="")
    observed_card_prefix = models.CharField(max_length=16, blank=True, default="")
    card_last4 = models.CharField(max_length=4, blank=True, default="")
    card_fingerprint = models.CharField(max_length=128, blank=True, default="")
    iban_bank_code = models.CharField(max_length=3, blank=True, default="")
    iban_fingerprint = models.CharField(max_length=128, blank=True, default="")
    card_luhn_valid = models.BooleanField(default=False)
    iban_checksum_valid = models.BooleanField(default=False)
    card_bank_known = models.BooleanField(default=False)
    iban_bank_known = models.BooleanField(default=False)
    banks_match = models.BooleanField(default=False)
    card_ownership_verified = models.BooleanField(default=False)
    iban_ownership_verified = models.BooleanField(default=False)
    result = models.CharField(max_length=30, choices=RESULT_CHOICES, default=RESULT_INVALID_CARD)
    failure_reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["result", "created_at"]),
            models.Index(fields=["card_prefix", "card_last4"]),
        ]

    def __str__(self):
        return f"{self.result} - {self.card_last4 or self.iban_bank_code or self.user_id}"


class BankAccount(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("needs_correction", "Needs Correction"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bank_accounts")
    bank = models.ForeignKey(IranianBank, on_delete=models.PROTECT, related_name="accounts")
    owner_name = models.CharField(max_length=255)
    card_number = models.CharField(max_length=16)
    iban = models.CharField(max_length=26)
    account_number = models.CharField(max_length=20, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    preferred = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "preferred"]),
            models.Index(fields=["card_number"]),
            models.Index(fields=["iban"]),
        ]

    def __str__(self):
        return f"{self.user.phone_number} - {self.card_number}"

    @property
    def is_usable(self):
        return self.status == "verified"

    def approve(self):
        if self.status != "pending":
            raise ValidationError(
                "حساب بانکی در وضعیت قابل تأیید نیست."
            )

        self.status = "verified"
        self.rejection_reason = ""
        self.verified_at = timezone.now()

        self.save(update_fields=[
            "status",
            "rejection_reason",
            "verified_at",
        ])

    def reject(self, reason):
        if self.status != "pending":
            raise ValidationError(
                "حساب بانکی در وضعیت قابل رد نیست."
            )

        self.status = "rejected"
        self.rejection_reason = reason
        self.verified_at = None
        self.preferred = False

        self.save(update_fields=[
            "status",
            "rejection_reason",
            "verified_at",
            "preferred",
        ])
