from apps.accounts.models import User
from django.test import TestCase

from .models import LoginHistory, SecurityEvent


class SecurityModelTests(TestCase):
    def test_security_event_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456781",
            password="Secret123!",
            full_name="Security User",
        )

        event = SecurityEvent.objects.create(
            user=user,
            event_type="login",
            description="Successful login",
        )

        self.assertEqual(event.user, user)
        self.assertEqual(event.event_type, "login")

    def test_login_history_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456782",
            password="Secret123!",
            full_name="History User",
        )

        login = LoginHistory.objects.create(
            user=user,
            user_agent="TestAgent",
            success=True,
        )

        self.assertTrue(login.success)
