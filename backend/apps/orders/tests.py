from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.assets.models import Asset
from .models import Order


class OrderModelTests(TestCase):
    def test_order_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456780",
            password="Secret123!",
            full_name="Order User",
        )

        asset = Asset.objects.create(
            symbol="ETH",
            name="Ethereum",
            decimals=18,
        )

        order = Order.objects.create(
            user=user,
            asset=asset,
            side="buy",
            order_type="limit",
            amount=Decimal("2.000000"),
            price=Decimal("3500.000000"),
            status="open",
        )

        self.assertEqual(order.user, user)
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.status, "open")