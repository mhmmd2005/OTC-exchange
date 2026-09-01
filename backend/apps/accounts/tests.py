from django.contrib.auth.password_validation import validate_password
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import OTPVerification, User
from apps.accounts.services.auth import AuthService
from apps.accounts.services.otp import get_otp_code


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_phone_normalization(self):
        self.assertEqual(AuthService.normalize_phone("09123456789"), "+989123456789")
        self.assertEqual(AuthService.normalize_phone("+989123456789"), "+989123456789")

    def test_request_login_otp_for_existing_phone(self):
        User.objects.create_user(phone_number="+989123456789", password="StrongPass123!", full_name="Existing User")

        response = self.client.post("/api/v1/auth/request-login-otp/", {"phone_number": "09123456789"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["allowed"])
        self.assertIn("challenge_id", response.data)
        self.assertEqual(response.data["next_step"], "otp")

    def test_request_login_otp_for_unknown_phone(self):
        response = self.client.post("/api/v1/auth/request-login-otp/", {"phone_number": "09123456789"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["allowed"])
        self.assertFalse(response.data["account_exists"])
        self.assertEqual(response.data["next_step"], "registration")
        self.assertEqual(response.data["phone_number"], "+989123456789")
        self.assertFalse(OTPVerification.objects.filter(phone_number="+989123456789", purpose="login").exists())

    def test_request_registration_otp(self):
        response = self.client.post("/api/v1/auth/request-registration-otp/", {"phone_number": "09123456789"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("challenge_id", response.data)
        self.assertEqual(OTPVerification.objects.get(id=response.data["challenge_id"]).purpose, "registration")

    def test_registration_flow_requires_confirm_password(self):
        response = self.client.post("/api/v1/auth/request-registration-otp/", {"phone_number": "09123456789"}, format="json")
        challenge_id = response.data["challenge_id"]
        otp = get_otp_code(challenge_id)
        otp_response = self.client.post("/api/v1/auth/verify-otp/", {"challenge_id": challenge_id, "otp": otp}, format="json")
        self.assertEqual(otp_response.status_code, 200)

        response = self.client.post(
            "/api/v1/auth/register/set-password/",
            {"flow_token": otp_response.data["flow_token"], "password": "StrongPass123!", "confirm_password": "DifferentPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_login_requires_otp_then_password(self):
        response = self.client.post("/api/v1/auth/login/verify-password/", {"flow_token": "bad", "password": "StrongPass123!"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_password_validator_rejects_weak_password(self):
        with self.assertRaises(Exception):
            validate_password("12345678")
