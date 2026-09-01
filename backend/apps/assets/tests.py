from django.test import TestCase

from .models import Asset


class AssetModelTests(TestCase):
    def test_asset_creation(self):
        asset = Asset.objects.create(symbol="BTC", name="Bitcoin", decimals=8)

        self.assertEqual(asset.symbol, "BTC")
        self.assertTrue(asset.is_active)
        self.assertEqual(asset.decimals, 8)
