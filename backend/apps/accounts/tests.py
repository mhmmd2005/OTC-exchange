from unittest import mock

from django.contrib.auth.password_validation import validate_password
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import BankCardPrefix, BankVerificationObservation, IranianBank, OTPVerification, User
from apps.accounts.services.auth import AuthService
from apps.accounts.services.bank_registry import create_bank_verification_observation
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


class RegistrySafetyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="+989123456789", password="StrongPass123!", full_name="Test User")
        self.bank = IranianBank.objects.create(name_fa="بانک تست", name_en="Test Bank", sheba_code="123", is_active=True)
        self.prefix = BankCardPrefix.objects.create(bank=self.bank, prefix="621986", source="trusted_registry", source_url="https://source-a.example/registry.json", is_active=True)

    def test_source_fetch_failure_does_not_write_database(self):
        before = IranianBank.objects.count()
        with mock.patch("apps.accounts.management.commands.sync_bank_registry.request.urlopen", side_effect=Exception("boom")):
            with self.assertRaises(CommandError):
                call_command("sync_bank_registry", source_url="https://source-a.example/registry.json")
        self.assertEqual(IranianBank.objects.count(), before)
        self.assertEqual(BankCardPrefix.objects.count(), 1)

    def test_invalid_json_does_not_write_database(self):
        with mock.patch("apps.accounts.management.commands.sync_bank_registry.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = b"{not json}"
            with self.assertRaises(CommandError):
                call_command("sync_bank_registry", source_url="https://source-a.example/registry.json")
        self.assertEqual(IranianBank.objects.count(), 1)
        self.assertEqual(BankCardPrefix.objects.count(), 1)

    def test_empty_payload_fails_safely(self):
        with mock.patch("apps.accounts.management.commands.sync_bank_registry.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = b"{}"
            with self.assertRaises(CommandError):
                call_command("sync_bank_registry", source_url="https://source-a.example/registry.json")
        self.assertEqual(BankCardPrefix.objects.count(), 1)

    def test_dry_run_does_not_change_database(self):
        before_prefixes = list(BankCardPrefix.objects.values_list("prefix", flat=True))
        with mock.patch("apps.accounts.management.commands.sync_bank_registry.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = (
                '{"banks": [{"name_fa": "Bank Test 2", "name_en": "Test Bank 2", "sheba_code": "456", "card_prefixes": ["62198619"]}]}'
            ).encode("utf-8")
            call_command("sync_bank_registry", source_url="https://source-b.example/registry.json", dry_run=True)
        self.assertEqual(list(BankCardPrefix.objects.values_list("prefix", flat=True)), before_prefixes)

    def test_source_a_cannot_deactivate_source_b_records(self):
        source_b = BankCardPrefix.objects.create(bank=self.bank, prefix="62198619", source="trusted_registry", source_url="https://source-b.example/registry.json", is_active=True)
        with mock.patch("apps.accounts.management.commands.sync_bank_registry.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = (
                '{"banks": [{"name_fa": "Bank Test", "name_en": "Test Bank", "sheba_code": "123", "card_prefixes": ["621986"]}]}'
            ).encode("utf-8")
            call_command("sync_bank_registry", source_url="https://source-a.example/registry.json")
        source_b.refresh_from_db()
        self.assertTrue(source_b.is_active)

    def test_unknown_user_input_only_creates_observation(self):
        before = BankCardPrefix.objects.count()
        create_bank_verification_observation(
            user=self.user,
            card_number="6219861999999999",
            iban="IR820120000000000000000000",
            card_luhn_valid=False,
            iban_checksum_valid=False,
            result=BankVerificationObservation.RESULT_UNKNOWN_CARD_PREFIX,
            failure_reason="card_prefix_unknown",
            observed_card_prefix="6219861999",
        )
        self.assertEqual(BankCardPrefix.objects.count(), before)
        self.assertEqual(BankVerificationObservation.objects.count(), 1)
        obs = BankVerificationObservation.objects.get()
        self.assertEqual(obs.result, BankVerificationObservation.RESULT_UNKNOWN_CARD_PREFIX)
        self.assertEqual(obs.observed_card_prefix, "6219861999")
