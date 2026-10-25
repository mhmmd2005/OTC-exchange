from __future__ import annotations

from django.conf import settings

from .base import PaymentGateway
from .nexpal import NexPalGateway
from .test_nexpal import TestNexPalGateway
from .zarinpal import ZarinPalGateway


def get_payment_gateway() -> PaymentGateway:
    configured = str(
        getattr(
            settings,
            "PAYMENT_GATEWAY",
            "",
        )
    ).strip().lower()

    if configured in {
        "test",
        "test_nexpal",
        "sandbox",
    }:
        return TestNexPalGateway()

    if configured in {"zarinpal", "zarinpal_sandbox"}:
        return ZarinPalGateway()

    if configured == "nexpal":
        return NexPalGateway()

    if getattr(
        settings,
        "DEBUG",
        False,
    ):
        return TestNexPalGateway()

    return NexPalGateway()