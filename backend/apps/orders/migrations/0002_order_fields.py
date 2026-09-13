from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="order_number",
            field=models.CharField(
                max_length=50,
                default="",
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="rate_toman",
            field=models.DecimalField(
                max_digits=24,
                decimal_places=8,
                default=0,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="fee_toman",
            field=models.DecimalField(
                max_digits=24,
                decimal_places=8,
                default=0,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="final_toman_amount",
            field=models.DecimalField(
                max_digits=24,
                decimal_places=8,
                default=0,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_source",
            field=models.CharField(
                max_length=255,
                blank=True,
                default="",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="destination",
            field=models.CharField(
                max_length=255,
                blank=True,
                default="",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="completed_at",
            field=models.DateTimeField(
                null=True,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="side",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("buy", "Buy"),
                    ("sell", "Sell"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("pending_payment", "Pending Payment"),
                    ("payment_confirmed", "Payment Confirmed"),
                    ("processing", "Processing"),
                    ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                    ("failed", "Failed"),
                    ("expired", "Expired"),
                ],
                default="pending_payment",
            ),
        ),
    ]