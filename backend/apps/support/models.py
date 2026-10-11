from django.db import models

from apps.accounts.models import User
from apps.admin_panel.models import AdminUser


class Ticket(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("pending", "Pending"), ("resolved", "Resolved"), ("closed", "Closed")]
    PRIORITY_CHOICES = [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")]
    CATEGORY_CHOICES = [
        ("trade", "Trading"),
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("verification", "Verification"),
        ("bank", "Bank"),
        ("security", "Security"),
        ("technical", "Technical"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"]), models.Index(fields=["priority", "status"])]

    def __str__(self):
        return f"{self.user.email} - {self.subject}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    # پیام ارسال‌شده توسط کاربر عادی
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ticket_messages",
        null=True,
        blank=True,
    )

    # پیام ارسال‌شده توسط ادمین
    admin_sender = models.ForeignKey(
        AdminUser,
        on_delete=models.CASCADE,
        related_name="support_ticket_messages",
        null=True,
        blank=True,
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["created_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                        models.Q(
                            sender__isnull=False,
                            admin_sender__isnull=True,
                        )
                        | models.Q(
                    sender__isnull=True,
                    admin_sender__isnull=False,
                )
                ),
                name="ticket_message_exactly_one_sender",
            ),
        ]

    def __str__(self):
        if self.admin_sender_id:
            author = (
                    self.admin_sender.full_name
                    or self.admin_sender.email
            )
        elif self.sender_id:
            author = (
                    self.sender.full_name
                    or self.sender.phone_number
            )
        else:
            author = "Unknown"

        return f"Message from {author} on {self.ticket.subject}"


class FAQ(models.Model):
    category = models.CharField(
        max_length=20,
        choices=Ticket.CATEGORY_CHOICES,
        default="other",
    )
    question = models.CharField(max_length=255)
    answer = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "سؤال متداول"
        verbose_name_plural = "سؤالات متداول"

    def __str__(self):
        return self.question
