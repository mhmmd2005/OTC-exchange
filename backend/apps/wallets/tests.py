from decimal import Decimal

from apps.accounts.models import User
from apps.assets.models import Asset
from django.test import TestCase

from .models import Wallet


class WalletModelTests(TestCase):
    def test_wallet_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456787",
            password="Secret123!",
            full_name="Wallet User",
        )

        asset = Asset.objects.create(
            symbol="USDT",
            name="Tether",
            decimals=6,
        )

        wallet = Wallet.objects.create(
            user=user,
            asset=asset,
            balance=Decimal("1.500000"),
            available_balance=Decimal("1.500000"),
            locked_balance=Decimal("0.000000"),
        )

        self.assertEqual(wallet.user, user)
        self.assertEqual(wallet.asset, asset)
        self.assertEqual(
            wallet.available_balance,
            Decimal("1.500000"),
        )
