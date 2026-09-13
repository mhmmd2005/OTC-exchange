from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("otc", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="otcquote",
            name="input_side",
            field=models.CharField(
                choices=[
                    ("toman", "Toman"),
                    ("crypto", "Crypto"),
                ],
                default="toman",
                max_length=10,
            ),
        ),
        migrations.RenameField(
            model_name="otcquote",
            old_name="quoted_price",
            new_name="rate_toman",
        ),
        migrations.RenameField(
            model_name="otcquote",
            old_name="quoted_total",
            new_name="toman_amount",
        ),
        migrations.AddField(
            model_name="otcquote",
            name="crypto_amount",
            field=models.DecimalField(
                decimal_places=8,
                default=Decimal("0"),
                max_digits=24,
            ),
        ),
        migrations.AddField(
            model_name="otcquote",
            name="fee_toman",
            field=models.DecimalField(
                decimal_places=8,
                default=Decimal("0"),
                max_digits=24,
            ),
        ),
        migrations.AddField(
            model_name="otcquote",
            name="fee_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=5,
            ),
        ),
        migrations.AddField(
            model_name="otcquote",
            name="final_toman_amount",
            field=models.DecimalField(
                decimal_places=8,
                default=Decimal("0"),
                max_digits=24,
            ),
        ),
        migrations.AddField(
            model_name="otcquote",
            name="minimum_toman",
            field=models.DecimalField(
                decimal_places=8,
                default=Decimal("0"),
                max_digits=24,
            ),
        ),
        migrations.AddField(
            model_name="otcquote",
            name="maximum_toman",
            field=models.DecimalField(
                decimal_places=8,
                default=Decimal("0"),
                max_digits=24,
            ),
        ),
    ]