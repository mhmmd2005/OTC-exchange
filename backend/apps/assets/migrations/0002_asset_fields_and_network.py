from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="name_fa",
            field=models.CharField(default="", max_length=255),
        ),
        migrations.AddField(
            model_name="asset",
            name="icon_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="asset",
            name="color",
            field=models.CharField(default="#6366f1", max_length=7),
        ),
        migrations.AddField(
            model_name="asset",
            name="price_precision",
            field=models.PositiveSmallIntegerField(default=2),
        ),
        migrations.AddField(
            model_name="asset",
            name="amount_precision",
            field=models.PositiveSmallIntegerField(default=8),
        ),
        migrations.AddField(
            model_name="asset",
            name="buy_price_toman",
            field=models.DecimalField(
                decimal_places=8,
                default=0,
                max_digits=24,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="sell_price_toman",
            field=models.DecimalField(
                decimal_places=8,
                default=0,
                max_digits=24,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="change_24h_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="high_24h_toman",
            field=models.DecimalField(
                decimal_places=8,
                default=0,
                max_digits=24,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="low_24h_toman",
            field=models.DecimalField(
                decimal_places=8,
                default=0,
                max_digits=24,
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="tradable",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="asset",
            name="deposit_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="asset",
            name="withdrawal_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name="AssetNetwork",
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
                ("code", models.CharField(max_length=16)),
                ("name", models.CharField(max_length=255)),
                ("display_name", models.CharField(default="", max_length=255)),
                (
                    "address_regex",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                    ),
                ),
                ("memo_required", models.BooleanField(default=False)),
                ("deposit_enabled", models.BooleanField(default=True)),
                ("withdrawal_enabled", models.BooleanField(default=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("congested", "Congested"),
                            ("maintenance", "Maintenance"),
                            ("disabled", "Disabled"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("confirmations", models.PositiveSmallIntegerField(default=1)),
                (
                    "estimated_arrival_minutes",
                    models.PositiveSmallIntegerField(default=30),
                ),
                (
                    "minimum_deposit",
                    models.DecimalField(
                        decimal_places=8,
                        default=0,
                        max_digits=24,
                    ),
                ),
                (
                    "minimum_withdrawal",
                    models.DecimalField(
                        decimal_places=8,
                        default=0,
                        max_digits=24,
                    ),
                ),
                (
                    "withdrawal_fee",
                    models.DecimalField(
                        decimal_places=8,
                        default=0,
                        max_digits=24,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="networks",
                        to="assets.asset",
                    ),
                ),
            ],
            options={
                "ordering": ["code"],
                "indexes": [
                    models.Index(
                        fields=["asset", "code"],
                        name="assets_assetn_asset_i_4d5b19_idx",
                    ),
                    models.Index(
                        fields=["status"],
                        name="assets_assetn_status_2c1dbb_idx",
                    ),
                ],
            },
        ),
        migrations.AddIndex(
            model_name="asset",
            index=models.Index(
                fields=["symbol"],
                name="assets_asset_symbol_71b57b_idx",
            ),
        ),
    ]