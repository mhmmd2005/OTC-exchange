from django.conf import settings

from .base import (
    PayoutGateway,
    PayoutGatewayError,
    PayoutResult,
)
from .test_payout import TestPayoutGateway


def get_payout_gateway() -> PayoutGateway:
    configured = (
        str(
            getattr(
                settings,
                "PAYOUT_GATEWAY",
                "",
            )
        )
        .strip()
        .lower()
    )

    if configured in {
        "test",
        "test_payout",
        "sandbox",
    }:
        return TestPayoutGateway()

    if getattr(settings, "DEBUG", False):
        return TestPayoutGateway()

    raise RuntimeError(
        "No production payout gateway is configured."
    )


__all__ = [
    "PayoutGateway",
    "PayoutGatewayError",
    "PayoutResult",
    "TestPayoutGateway",
    "get_payout_gateway",
]