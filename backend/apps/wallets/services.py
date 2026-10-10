from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.assets.models import Asset

from .models import Wallet


class WalletService:
    """Wallet-level helper operations."""

    @staticmethod
    def ensure_positive_balance(
        balance,
    ):
        return max(
            balance,
            0,
        )


class InsufficientWalletBalance(ValueError):
    """Raised when the wallet does not have enough available balance."""

@transaction.atomic
def provision_user_wallets(
    user,
):
    """
    Ensure the user has exactly one wallet
    for every active asset.

    This operation only creates zero-balance
    wallet accounts.
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


@transaction.atomic
def credit_wallet(
    *,
    user_id,
    asset_id,
    amount: Decimal,
) -> Wallet:
    """
    Atomically credit a user's wallet.

    This helper must be called only for a confirmed
    financial settlement.

    Both balance and available_balance are increased.
    locked_balance is intentionally unchanged.
    """
    if amount <= 0:
        raise ValueError(
            "Wallet credit amount must be positive.",
        )

    wallet = (
        Wallet.objects
        .select_for_update()
        .get(
            user_id=user_id,
            asset_id=asset_id,
        )
    )

    wallet.balance += amount

    wallet.available_balance += amount

    wallet.save(
        update_fields=[
            "balance",
            "available_balance",
            "updated_at",
        ],
    )

    return wallet


@transaction.atomic
def lock_wallet(
    *,
    user_id,
    asset_id,
    amount: Decimal,
) -> Wallet:
    """
    Move an amount from available balance to locked balance.

    The total balance remains unchanged.
    """
    if amount <= 0:
        raise ValueError(
            "Wallet lock amount must be positive.",
        )

    wallet = (
        Wallet.objects
        .select_for_update()
        .get(
            user_id=user_id,
            asset_id=asset_id,
        )
    )

    if wallet.available_balance < amount:
        raise InsufficientWalletBalance(
            "Insufficient available wallet balance.",
        )

    wallet.available_balance -= amount
    wallet.locked_balance += amount

    wallet.save(
        update_fields=[
            "available_balance",
            "locked_balance",
            "updated_at",
        ],
    )

    return wallet


@transaction.atomic
def release_locked_wallet(
    *,
    user_id,
    asset_id,
    amount: Decimal,
) -> Wallet:
    """
    Return a previously locked amount to available balance.

    The total balance remains unchanged.
    """
    if amount <= 0:
        raise ValueError(
            "Wallet release amount must be positive.",
        )

    wallet = (
        Wallet.objects
        .select_for_update()
        .get(
            user_id=user_id,
            asset_id=asset_id,
        )
    )

    if wallet.locked_balance < amount:
        raise ValueError(
            "Wallet locked balance is insufficient.",
        )

    wallet.locked_balance -= amount
    wallet.available_balance += amount

    wallet.save(
        update_fields=[
            "available_balance",
            "locked_balance",
            "updated_at",
        ],
    )

    return wallet


@transaction.atomic
def complete_locked_wallet(
    *,
    user_id,
    asset_id,
    amount: Decimal,
) -> Wallet:
    """
    Permanently debit a previously locked amount.

    This reduces total balance and locked balance.
    """
    if amount <= 0:
        raise ValueError(
            "Wallet settlement amount must be positive.",
        )

    wallet = (
        Wallet.objects
        .select_for_update()
        .get(
            user_id=user_id,
            asset_id=asset_id,
        )
    )

    if wallet.locked_balance < amount:
        raise ValueError(
            "Wallet locked balance is insufficient.",
        )

    if wallet.balance < amount:
        raise ValueError(
            "Wallet total balance is insufficient.",
        )

    wallet.locked_balance -= amount
    wallet.balance -= amount

    wallet.save(
        update_fields=[
            "balance",
            "locked_balance",
            "updated_at",
        ],
    )

    return wallet