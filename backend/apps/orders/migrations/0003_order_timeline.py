from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderTimeline",
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
                ("status", models.CharField(max_length=20)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("occurred_at", models.DateTimeField(blank=True, null=True)),
                ("completed", models.BooleanField(default=False)),
                ("current", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="timeline",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]