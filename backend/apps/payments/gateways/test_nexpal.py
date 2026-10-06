from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from django.conf import settings

from .base import (
    CreatePaymentResult,
    PaymentGateway,
    PaymentGatewayError,
    TransactionResult,
    VerifyPaymentResult,
)


@dataclass
class _TestPaymentState:
    invoice_id: str
    amount_rial: int
    paid: bool = False
    verified: bool = False
    reference_number: str = ""


class TestNexPalGateway(PaymentGateway):
    """
    Local development test double for NexPal.

    This gateway never contacts NexPal.

    It simulates:
        create
        payment
        transaction inquiry
        verify
        reverse
    """

    name = "test_nexpal"

    _payments: ClassVar[
        dict[str, _TestPaymentState]
    ] = {}

    @staticmethod
    def _build_token(
        *,
        invoice_id: str,
        amount_rial: int,
    ) -> str:
        raw = (
            f"{invoice_id}|{amount_rial}"
        ).encode("utf-8")

        encoded = (
            base64.urlsafe_b64encode(
                raw,
            )
            .decode("ascii")
            .rstrip("=")
        )

        return (
            "sandbox_"
            + encoded
        )

    @staticmethod
    def _decode_token(
        token: str,
    ) -> tuple[str, int]:
        if not token.startswith("sandbox_"):
            raise PaymentGatewayError(
                "Test payment token is invalid.",
                code=14,
            )

        encoded = token.removeprefix(
            "sandbox_",
        )

        padding = (
            "="
            * (
                -len(encoded)
                % 4
            )
        )

        try:
            raw = base64.urlsafe_b64decode(
                encoded + padding,
            ).decode("utf-8")
        except (
            ValueError,
            UnicodeDecodeError,
        ) as exc:
            raise PaymentGatewayError(
                "Test payment token is invalid.",
                code=14,
            ) from exc

        try:
            invoice_id, amount = (
                raw.split(
                    "|",
                    1,
                )
            )
            amount_rial = int(amount)
        except (
            ValueError,
        ) as exc:
            raise PaymentGatewayError(
                "Test payment token is invalid.",
                code=14,
            ) from exc

        if not invoice_id or amount_rial <= 0:
            raise PaymentGatewayError(
                "Test payment token is invalid.",
                code=14,
            )

        return invoice_id, amount_rial

    @staticmethod
    def _reference_number(
        token: str,
    ) -> str:
        digest = hashlib.sha256(
            token.encode("utf-8"),
        ).hexdigest()

        return (
            "TEST-"
            + digest[:18].upper()
        )

    def _build_pay_url(
        self,
        token: str,
    ) -> str:
        base_url = str(
            getattr(
                settings,
                "TEST_NEXPAL_PAYMENT_URL_BASE",
                "http://127.0.0.1:5173/payment-test",
            )
        ).rstrip("/")

        return f"{base_url}/{token}"

    def create_payment(
        self,
        *,
        idempotency_key: str,
        invoice_id: str,
        amount_toman: Decimal,
        description: str,
        mobile: str = "",
        email: str = "",
        national_code: str = "",
    ) -> CreatePaymentResult:
        amount_rial = int(
            amount_toman
            * Decimal("10")
        )

        if amount_rial < 1:
            raise PaymentGatewayError(
                "Test payment amount is invalid.",
                code=10,
            )

        token = self._build_token(
            invoice_id=invoice_id,
            amount_rial=amount_rial,
        )

        self._payments[token] = (
            _TestPaymentState(
                invoice_id=invoice_id,
                amount_rial=amount_rial,
                reference_number=(
                    self._reference_number(
                        token,
                    )
                ),
            )
        )

        return CreatePaymentResult(
            token=token,
            invoice_id=invoice_id,
            amount_rial=amount_rial,
            pay_url=self._build_pay_url(
                token,
            ),
            code=100,
            message="Success",
        )

    def register_existing_payment(
        self,
        *,
        token: str,
        invoice_id: str,
        amount_rial: int,
    ) -> None:
        token = str(
            token or ""
        ).strip()

        if not token:
            raise PaymentGatewayError(
                "Test payment token is required.",
                code=14,
            )

        state = self._payments.get(
            token,
        )

        if state is not None:
            if (
                state.invoice_id
                != invoice_id
                or state.amount_rial
                != amount_rial
            ):
                raise PaymentGatewayError(
                    "Existing test payment payload does not match.",
                    code=20,
                )

            return

        self._payments[token] = (
            _TestPaymentState(
                invoice_id=invoice_id,
                amount_rial=amount_rial,
                reference_number=(
                    self._reference_number(
                        token,
                    )
                ),
            )
        )

    def simulate_successful_payment(
        self,
        *,
        token: str,
    ) -> str:
        token = str(
            token or ""
        ).strip()

        state = self._payments.get(
            token,
        )

        if state is None:
            raise PaymentGatewayError(
                "Test payment was not initialized.",
                code=14,
            )

        state.paid = True

        return state.reference_number

    def get_transaction(
        self,
        *,
        token: str,
    ) -> TransactionResult:
        token = str(
            token or ""
        ).strip()

        state = self._payments.get(
            token,
        )

        if state is None:
            try:
                invoice_id, amount_rial = (
                    self._decode_token(
                        token,
                    )
                )
            except PaymentGatewayError:
                raise

            state = _TestPaymentState(
                invoice_id=invoice_id,
                amount_rial=amount_rial,
                reference_number=(
                    self._reference_number(
                        token,
                    )
                ),
            )

            self._payments[token] = state

        if not state.paid:
            return TransactionResult(
                code=12,
                message="pending",
                invoice_id=state.invoice_id,
                amount_rial=state.amount_rial,
            )

        return TransactionResult(
            code=100,
            message="verified",
            invoice_id=state.invoice_id,
            reference_number=state.reference_number,
            request_date="",
            amount_rial=state.amount_rial,
            description="Test payment",
        )

    def verify_payment(
        self,
        *,
        token: str,
    ) -> VerifyPaymentResult:
        token = str(
            token or ""
        ).strip()

        state = self._payments.get(
            token,
        )

        if state is None:
            raise PaymentGatewayError(
                "Test payment was not initialized.",
                code=14,
            )

        if not state.paid:
            return VerifyPaymentResult(
                code=12,
                message="pending",
                invoice_id=state.invoice_id,
                amount_rial=state.amount_rial,
            )

        if state.verified:
            return VerifyPaymentResult(
                code=13,
                message="already verified",
                invoice_id=state.invoice_id,
                reference_number=(
                    state.reference_number
                ),
                amount_rial=state.amount_rial,
            )

        state.verified = True

        return VerifyPaymentResult(
            code=100,
            message="verified",
            invoice_id=state.invoice_id,
            reference_number=(
                state.reference_number
            ),
            amount_rial=state.amount_rial,
            description="Test payment",
        )

    def reverse_payment(
        self,
        *,
        token: str,
    ) -> dict:
        token = str(
            token or ""
        ).strip()

        state = self._payments.get(
            token,
        )

        if state is None:
            raise PaymentGatewayError(
                "Test payment was not initialized.",
                code=14,
            )

        if not state.verified:
            raise PaymentGatewayError(
                "Test payment cannot be reversed before verification.",
                code=12,
            )

        state.paid = False
        state.verified = False

        return {
            "code": 100,
            "message": "reversed",
            "invoice": state.invoice_id,
            "referenceNumber": state.reference_number,
            "amount": state.amount_rial,
        }