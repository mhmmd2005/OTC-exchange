from decimal import Decimal

from apps.accounts.models import User
from apps.assets.models import Asset
from django.test import TestCase

from .models import Transaction


class TransactionModelTests(TestCase):
    def test_transaction_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456786",
            password="Secret123!",
            full_name="Tx User",
        )

        asset = Asset.objects.create(
            symbol="TRX",
            name="Tron",
            decimals=6,
        )

        transaction = Transaction.objects.create(
            user=user,
            asset=asset,
            transaction_type="deposit",
            amount=Decimal("10.000000"),
            fee=Decimal("0.020000"),
            network="TRC20",
            address="TAddress",
            txid="abc123",
            status="completed",
        )

        self.assertEqual(transaction.transaction_type, "deposit")
        self.assertEqual(transaction.status, "completed")
