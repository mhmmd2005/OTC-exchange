from apps.accounts.services.phone import normalize_phone_number
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


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
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ("not_started", "Not started"),
            ("in_progress", "In progress"),
            ("pending_review", "Pending review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="not_started",
    )
    kyc_level = models.CharField(max_length=20, default="basic")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [models.Index(fields=["phone_number"]), models.Index(fields=["kyc_status"])]

    def __str__(self):
        return self.phone_number


class OTPVerification(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login"
        REGISTRATION = "registration", "Registration"
        PASSWORD_RESET = "password_reset", "Password Reset"

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
    card_prefixes = models.JSONField(default=list)
    color = models.CharField(max_length=7, default="#6366f1")
    logo_url = models.URLField(blank=True, default="")

    class Meta:
        ordering = ["name_fa"]

    def __str__(self):
        return self.name_fa


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
