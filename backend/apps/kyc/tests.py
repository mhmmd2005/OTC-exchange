from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.services.session import create_session
from apps.assets.models import Asset
from apps.orders.models import Order
from apps.transactions.models import Transaction
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
        self.assertEqual(kyc.status, "pending_review")

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
        self.assertEqual(kyc.status, "approved")

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
        self.assertEqual(kyc.status, "rejected")


class KycApplicationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="+989123456789",
            password="Secret123!",
            full_name="Test User",
        )
        refresh = RefreshToken.for_user(self.user)
        session_id = create_session(self.user.id)
        refresh["session_id"] = session_id
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

    def test_verification_summary_daily_limits_use_real_usage(self):
        asset = Asset.objects.create(symbol="USDT", name="Tether", decimals=6)
        now = timezone.localtime()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        buy_order = Order.objects.create(
            user=self.user,
            asset=asset,
            side="buy",
            status="completed",
            final_toman_amount=Decimal("100000"),
        )
        Order.objects.filter(pk=buy_order.pk).update(created_at=day_start + timedelta(hours=1))

        failed_buy_order = Order.objects.create(
            user=self.user,
            asset=asset,
            side="buy",
            status="failed",
            final_toman_amount=Decimal("999999"),
        )
        Order.objects.filter(pk=failed_buy_order.pk).update(created_at=day_start + timedelta(hours=2))

        sell_order = Order.objects.create(
            user=self.user,
            asset=asset,
            side="sell",
            status="completed",
            final_toman_amount=Decimal("205000"),
        )
        Order.objects.filter(pk=sell_order.pk).update(created_at=day_start + timedelta(hours=3))

        crypto_withdrawal = Transaction.objects.create(
            user=self.user,
            asset=asset,
            transaction_type="crypto_withdrawal",
            status="completed",
            toman_amount=Decimal("75000"),
        )
        Transaction.objects.filter(pk=crypto_withdrawal.pk).update(created_at=day_start + timedelta(hours=4))

        cancelled_crypto_withdrawal = Transaction.objects.create(
            user=self.user,
            asset=asset,
            transaction_type="crypto_withdrawal",
            status="cancelled",
            toman_amount=Decimal("1234567"),
        )
        Transaction.objects.filter(pk=cancelled_crypto_withdrawal.pk).update(created_at=day_start + timedelta(hours=5))

        response = self.client.get("/api/v1/verification")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        limits = response.data["limits"]
        self.assertEqual(limits["usedBuy"], "100000")
        self.assertEqual(limits["usedSell"], "205000")
        self.assertEqual(limits["usedCryptoWithdrawalTomanEquivalent"], "75000")
        self.assertEqual(limits["dailyBuy"], str(settings.DAILY_BUY_LIMIT))
        self.assertEqual(limits["dailySell"], str(settings.DAILY_SELL_LIMIT))
        self.assertEqual(limits["dailyCryptoWithdrawalTomanEquivalent"], str(settings.DAILY_CRYPTO_WITHDRAWAL_TOMAN_LIMIT))

    def test_verification_summary_empty_history_returns_zeroes(self):
        response = self.client.get("/api/v1/verification")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        limits = response.data["limits"]
        self.assertEqual(limits["usedBuy"], "0")
        self.assertEqual(limits["usedSell"], "0")
        self.assertEqual(limits["usedCryptoWithdrawalTomanEquivalent"], "0")
        self.assertEqual(limits["dailyBuy"], str(settings.DAILY_BUY_LIMIT))
        self.assertEqual(limits["dailySell"], str(settings.DAILY_SELL_LIMIT))
        self.assertEqual(limits["dailyCryptoWithdrawalTomanEquivalent"], str(settings.DAILY_CRYPTO_WITHDRAWAL_TOMAN_LIMIT))


class AdminKycAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number="+989123456789",
            password="Secret123!",
            full_name="Test User",
        )
        self.admin_user = User.objects.create_user(
            phone_number="+989111111111",
            password="AdminPass123!",
            full_name="Admin User",
            is_staff=True,
        )
        user_refresh = RefreshToken.for_user(self.user)
        user_session_id = create_session(self.user.id)
        user_refresh["session_id"] = user_session_id
        self.user_token = str(user_refresh.access_token)
        admin_refresh = RefreshToken.for_user(self.admin_user)
        admin_session_id = create_session(self.admin_user.id)
        admin_refresh["session_id"] = admin_session_id
        self.admin_token = str(admin_refresh.access_token)

    def test_admin_can_list_kyc_applications(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.get("/api/v1/kyc/admin/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], kyc.id)

    def test_admin_can_filter_by_status(self):
        user2 = User.objects.create_user(
            phone_number="+989999999999",
            password="Secret123!",
            full_name="Test User 2",
        )
        KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        KycApplication.objects.create(
            user=user2,
            first_name="Jane",
            last_name="Smith",
            status="approved",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.get("/api/v1/kyc/admin/?status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "pending")

    def test_admin_can_get_kyc_detail(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.get(f"/api/v1/kyc/admin/{kyc.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], kyc.id)
        self.assertEqual(response.data["first_name"], "John")

    def test_non_admin_cannot_list_kyc_applications(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        response = self.client.get("/api/v1/kyc/admin/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_cannot_get_kyc_detail(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        response = self.client.get(f"/api/v1/kyc/admin/{kyc.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_admin_endpoints(self):
        self.client.credentials()
        response = self.client.get("/api/v1/kyc/admin/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_approve_pending_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.post(f"/api/v1/kyc/admin/{kyc.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kyc.refresh_from_db()
        self.assertEqual(kyc.status, "approved")
        self.assertEqual(kyc.reviewed_by, self.admin_user)
        self.assertIsNotNone(kyc.reviewed_at)
        self.user.refresh_from_db()
        self.assertEqual(kyc.status, "approved")

    def test_admin_cannot_approve_non_pending_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="approved",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.post(f"/api/v1/kyc/admin/{kyc.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_reject_pending_kyc_with_reason(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.post(
            f"/api/v1/kyc/admin/{kyc.id}/reject/",
            {"reason": "Document not clear"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kyc.refresh_from_db()
        self.assertEqual(kyc.status, "rejected")
        self.assertEqual(kyc.rejection_reason, "Document not clear")
        self.assertEqual(kyc.reviewed_by, self.admin_user)
        self.assertIsNotNone(kyc.reviewed_at)
        self.user.refresh_from_db()
        self.assertEqual(kyc.status, "rejected")

    def test_admin_cannot_reject_without_reason(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.post(f"/api/v1/kyc/admin/{kyc.id}/reject/", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_reject_non_pending_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="rejected",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.post(
            f"/api/v1/kyc/admin/{kyc.id}/reject/",
            {"reason": "Test reason"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_approve_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        response = self.client.post(f"/api/v1/kyc/admin/{kyc.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_cannot_reject_kyc(self):
        kyc = KycApplication.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            status="pending",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")
        response = self.client.post(
            f"/api/v1/kyc/admin/{kyc.id}/reject/",
            {"reason": "Test reason"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
