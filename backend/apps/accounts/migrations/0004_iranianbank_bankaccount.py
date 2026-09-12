from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_otpverification_purpose"),
    ]

    operations = [
        migrations.CreateModel(
            name="IranianBank",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name_fa", models.CharField(max_length=255)),
                ("name_en", models.CharField(max_length=255)),
                ("card_prefixes", models.JSONField(default=list)),
                ("color", models.CharField(max_length=32, blank=True, default="")),
                ("logo_url", models.URLField(blank=True, default="")),
            ],
            options={
                "ordering": ["name_fa"],
            },
        ),
        migrations.CreateModel(
            name="BankAccount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("owner_name", models.CharField(max_length=255)),
                ("card_number", models.CharField(max_length=32)),
                ("iban", models.CharField(max_length=34)),
                ("account_number", models.CharField(max_length=64, blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("verified", "Verified"),
                            ("needs_correction", "Needs Correction"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=32,
                    ),
                ),
                ("preferred", models.BooleanField(default=False)),
                ("rejection_reason", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                (
                    "bank",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="bank_accounts",
                        to="accounts.iranianbank",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bank_accounts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]