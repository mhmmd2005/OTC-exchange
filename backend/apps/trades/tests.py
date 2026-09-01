from decimal import Decimal

from apps.accounts.models import User
from apps.assets.models import Asset
from apps.orders.models import Order
from django.test import TestCase

from .models import Trade


class TradeModelTests(TestCase):
    def test_trade_creation(self):
        user = User.objects.create_user(
            phone_number="+989123456785",
            password="Secret123!",
            full_name="Trade User",
        )

        asset = Asset.objects.create(
            symbol="BTC",
            name="Bitcoin",
            decimals=8,
        )

        order = Order.objects.create(
            user=user,
            asset=asset,
            side="buy",
            order_type="limit",
            amount=Decimal("0.500000"),
            price=Decimal("60000.000000"),
            status="filled",
        )

        trade = Trade.objects.create(
            user=user,
            order=order,
            asset=asset,
            side="buy",
            amount=Decimal("0.500000"),
            execution_price=Decimal("60000.000000"),
            fee=Decimal("0.010000"),
            total=Decimal("30000.000000"),
        )

        self.assertEqual(trade.order, order)
        self.assertEqual(trade.fee, Decimal("0.010000"))
