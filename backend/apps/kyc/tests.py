from apps.accounts.models import User
from django.test import TestCase

from .models import KycApplication


class KycApplicationModelTests(TestCase):
    def test_kyc_application_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456789",
            password="Secret123!",
            full_name="KYC User",
        )

        application = KycApplication.objects.create(
            user=user,
            status="pending_review",
            level="tier_2",
        )

        self.assertEqual(application.user, user)
        self.assertEqual(application.status, "pending_review")
