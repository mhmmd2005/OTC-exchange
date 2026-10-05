from django.db import transaction

from apps.assets.models import Asset
from .models import Wallet


class WalletService:
    """Placeholder service for wallet validation workflows."""

    @staticmethod
    def ensure_positive_balance(balance):
        return max(balance, 0)


@transaction.atomic
def provision_user_wallets(user):
    """
    Ensure the user has exactly one wallet for every active asset.

    This operation only creates zero-balance wallet accounts.
    It never creates or moves funds.
    """
    assets = list(
        Asset.objects.filter(
            is_active=True,
        ).only("id")
    )

    if not assets:
        return

    Wallet.objects.bulk_create(
        [
            Wallet(
                user=user,
                asset=asset,
            )
            for asset in assets
        ],
        ignore_conflicts=True,
    )
