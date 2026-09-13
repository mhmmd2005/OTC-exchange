from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("assets", "0002_asset_fields_and_network"),
    ]

    operations = [
        migrations.CreateModel(
            name="Market",
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
                ("is_active", models.BooleanField(default=True)),
                (
                    "volume_24h_toman",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=30,
                    ),
                ),
                (
                    "last_price_toman",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=30,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "asset",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="market",
                        to="assets.asset",
                    ),
                ),
            ],
        ),
    ]