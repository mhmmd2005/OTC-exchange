from apps.accounts.models import User
from django.test import TestCase

from .models import Ticket, TicketMessage


class SupportModelTests(TestCase):
    def test_ticket_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456783",
            password="Secret123!",
            full_name="Support User",
        )

        ticket = Ticket.objects.create(
            user=user,
            subject="Wallet issue",
            category="wallet",
            priority="high",
        )

        self.assertEqual(ticket.user, user)
        self.assertEqual(ticket.status, "open")

    def test_ticket_message_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456784",
            password="Secret123!",
            full_name="Support User 2",
        )

        ticket = Ticket.objects.create(
            user=user,
            subject="Account issue",
            category="account",
        )

        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=user,
            message="I need help.",
        )

        self.assertEqual(message.ticket, ticket)
