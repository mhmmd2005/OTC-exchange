from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import KycApplication

User = get_user_model()


class KycApplicationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+989123456789",
            password="Secret123!",
            full_name="Test User",
        )

    def test_create_kyc_application(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            national_id="1234567890",
        )
        self.assertEqual(kyc.user, self.user)
        self.assertEqual(kyc.status, "not_started")
        self.assertTrue(kyc.can_edit)
        self.assertTrue(kyc.can_submit)

    def test_submit_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
        )
        kyc.submit()
        self.assertEqual(kyc.status, "pending")
        self.assertIsNotNone(kyc.submitted_at)
        self.assertFalse(kyc.can_edit)
        self.assertFalse(kyc.can_submit)
        self.user.refresh_from_db()
        self.assertEqual(self.user.kyc_status, "pending_review")

    def test_approve_kyc(self):
        admin_user = User.objects.create_user(
            phone_number="+989111111111",
            password="AdminPass123!",
            full_name="Admin User",
            is_staff=True,
        )
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        kyc.approve(reviewed_by=admin_user)
        self.assertEqual(kyc.status, "approved")
        self.assertIsNotNone(kyc.reviewed_at)
        self.assertEqual(kyc.reviewed_by, admin_user)
        self.assertFalse(kyc.can_edit)
        self.user.refresh_from_db()
        self.assertEqual(self.user.kyc_status, "approved")

    def test_reject_kyc(self):
        admin_user = User.objects.create_user(
            phone_number="+989111111111",
            password="AdminPass123!",
            full_name="Admin User",
            is_staff=True,
        )
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        reason = "ID document not clear"
        kyc.reject(reason, reviewed_by=admin_user)
        self.assertEqual(kyc.status, "rejected")
        self.assertEqual(kyc.rejection_reason, reason)
        self.assertIsNotNone(kyc.reviewed_at)
        self.assertTrue(kyc.can_edit)
        self.user.refresh_from_db()
        self.assertEqual(self.user.kyc_status, "rejected")


class KycApplicationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="+989123456789",
            password="Secret123!",
            full_name="Test User",
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_or_create_kyc(self):
        response = self.client.get("/api/v1/kyc/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)

    def test_submit_kyc_application(self):
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "national_id": "1234567890",
        }
        response = self.client.post("/api/v1/kyc/submit/", kyc_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "pending")
        self.assertIsNotNone(response.data["submitted_at"])

    def test_cannot_submit_pending_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        response = self.client.post("/api/v1/kyc/submit/", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_rejected_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="rejected",
            rejection_reason="Need clearer photo",
        )
        update_data = {"first_name": "Jane"}
        response = self.client.patch("/api/v1/kyc/update/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kyc.refresh_from_db()
        self.assertEqual(kyc.first_name, "Jane")

    def test_cannot_update_pending_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        response = self.client.patch("/api/v1/kyc/update/", {"first_name": "Jane"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_kyc_status(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        response = self.client.get("/api/v1/kyc/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "pending")

    def test_unauthenticated_cannot_access_kyc(self):
        self.client.credentials()
        response = self.client.get("/api/v1/kyc/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_manually_set_status_via_api(self):
        response = self.client.post(
            "/api/v1/kyc/submit/",
            {"status": "approved", "first_name": "John", "last_name": "Doe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kyc = KycApplication.objects.filter(user=self.user).first()
        self.assertEqual(kyc.status, "pending")

    def test_cannot_set_rejection_reason_via_api(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="rejected",
            rejection_reason="Original reason",
        )
        response = self.client.patch(
            "/api/v1/kyc/update/",
            {"rejection_reason": "New reason"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kyc.refresh_from_db()
        self.assertEqual(kyc.rejection_reason, "Original reason")
