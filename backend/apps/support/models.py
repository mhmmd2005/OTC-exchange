from django.db import models

from apps.accounts.models import User


class Ticket(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("pending", "Pending"), ("resolved", "Resolved"), ("closed", "Closed")]
    PRIORITY_CHOICES = [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")]
    CATEGORY_CHOICES = [("account", "Account"), ("wallet", "Wallet"), ("trading", "Trading"), ("security", "Security"), ("other", "Other")]

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
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ticket_messages")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender.email} on {self.ticket.subject}"
