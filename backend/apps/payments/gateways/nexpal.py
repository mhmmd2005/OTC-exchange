from __future__ import annotations

from decimal import Decimal

import requests
from django.conf import settings

from .base import (
    CreatePaymentResult,
    PaymentGateway,
    PaymentGatewayError,
    TransactionResult,
    VerifyPaymentResult,
)


class NexPalGateway(PaymentGateway):
    name = "nexpal"

    def __init__(self):
        self.api_key = str(
            getattr(
                settings,
                "NEXPAL_API_KEY",
                "",
            )
        ).strip()

        self.base_url = str(
            getattr(
                settings,
                "NEXPAL_BASE_URL",
                "https://api.nexpal.io/v1/payment",
            )
        ).rstrip("/")

        self.callback_url = str(
            getattr(
                settings,
                "NEXPAL_CALLBACK_URL",
                "",
            )
        ).strip()

        self.terminal_number = str(
            getattr(
                settings,
                "NEXPAL_TERMINAL_NUMBER",
                "",
            )
        ).strip()

        self.timeout = float(
            getattr(
                settings,
                "NEXPAL_TIMEOUT",
                15,
            )
        )

    def _post(
        self,
        path: str,
        payload: dict,
    ) -> dict:
        if not self.api_key:
            raise PaymentGatewayError(
                "NexPal API key is not configured.",
            )

        try:
            response = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )

        except requests.Timeout as exc:
            raise PaymentGatewayError(
                "NexPal request timed out.",
                retryable=True,
            ) from exc

        except requests.RequestException as exc:
            raise PaymentGatewayError(
                "NexPal request failed.",
                retryable=True,
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise PaymentGatewayError(
                "NexPal returned an invalid response.",
                http_status=response.status_code,
                retryable=response.status_code >= 500,
            ) from exc

        if not response.ok:
            raw_code = data.get("code")

            try:
                code = int(raw_code)
            except (
                TypeError,
                ValueError,
            ):
                code = None

            raise PaymentGatewayError(
                str(
                    data.get(
                        "description",
                        data.get(
                            "message",
                            "NexPal request failed.",
                        ),
                    )
                ),
                code=code,
                http_status=response.status_code,
                retryable=response.status_code
                in {429, 500, 502, 503},
            )

        return data

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
        if not self.api_key:
            raise PaymentGatewayError(
                "NexPal API key is not configured.",
            )

        if not self.callback_url:
            raise PaymentGatewayError(
                "NexPal callback URL is not configured.",
            )

        amount_rial_decimal = (
            amount_toman * Decimal("10")
        )

        if (
            amount_rial_decimal
            != amount_rial_decimal.to_integral_value()
        ):
            raise PaymentGatewayError(
                "NexPal amount must be an integer in Rial.",
            )

        amount_rial = int(
            amount_rial_decimal
        )

        payload = {
            "apiKey": self.api_key,
            "idempotencyKey": idempotency_key,
            "amount": amount_rial,
            "callbackUrl": self.callback_url,
            "invoiceId": invoice_id,
            "description": description[:255],
        }

        if self.terminal_number:
            payload["terminalNumber"] = (
                self.terminal_number
            )

        if mobile:
            payload["mobile"] = mobile

        if email:
            payload["email"] = email.lower()

        if national_code:
            payload["nationalCode"] = national_code

        data = self._post(
            "/create",
            payload,
        )

        try:
            code = int(
                data.get("code")
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise PaymentGatewayError(
                "NexPal returned an invalid response code.",
            ) from exc

        if code != 100:
            raise PaymentGatewayError(
                str(
                    data.get(
                        "description",
                        "NexPal payment creation failed.",
                    )
                ),
                code=code,
            )

        token = str(
            data.get(
                "token",
                "",
            )
        ).strip()

        returned_invoice_id = str(
            data.get(
                "invoiceId",
                "",
            )
        ).strip()

        pay_url = str(
            data.get(
                "payUrl",
                "",
            )
        ).strip()

        if not token:
            raise PaymentGatewayError(
                "NexPal response did not contain a token.",
            )

        if not returned_invoice_id:
            raise PaymentGatewayError(
                "NexPal response did not contain invoiceId.",
            )

        if not pay_url:
            raise PaymentGatewayError(
                "NexPal response did not contain payUrl.",
            )

        try:
            returned_amount = int(
                data.get(
                    "amount",
                    amount_rial,
                )
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise PaymentGatewayError(
                "NexPal returned an invalid amount.",
            ) from exc

        if returned_amount != amount_rial:
            raise PaymentGatewayError(
                "NexPal returned an unexpected amount.",
            )

        return CreatePaymentResult(
            token=token,
            invoice_id=returned_invoice_id,
            amount_rial=returned_amount,
            pay_url=pay_url,
            code=code,
            message=str(
                data.get(
                    "description",
                    "Success",
                )
            ),
        )

    def get_transaction(
        self,
        *,
        token: str,
    ) -> TransactionResult:
        token = str(
            token or ""
        ).strip()

        if not token:
            raise PaymentGatewayError(
                "NexPal transaction token is required.",
            )

        data = self._post(
            "/transaction",
            {
                "apiKey": self.api_key,
                "token": token,
            },
        )

        try:
            code = int(
                data.get("code")
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise PaymentGatewayError(
                "NexPal returned an invalid transaction code.",
            ) from exc

        return TransactionResult(
            code=code,
            message=str(
                data.get(
                    "message",
                    "",
                )
            ),
            invoice_id=str(
                data.get(
                    "invoice",
                    "",
                )
            ),
            reference_number=str(
                data.get(
                    "referenceNumber",
                    "",
                )
            ),
            masked_card_number=str(
                data.get(
                    "maskedCardNumber",
                    "",
                )
            ),
            hashed_card_number=str(
                data.get(
                    "hashedCardNumber",
                    "",
                )
            ),
            request_date=str(
                data.get(
                    "requestDate",
                    "",
                )
            ),
            amount_rial=int(
                data.get(
                    "amount",
                    0,
                )
                or 0
            ),
            description=str(
                data.get(
                    "description",
                    "",
                )
            ),
        )

    def verify_payment(
        self,
        *,
        token: str,
    ) -> VerifyPaymentResult:
        token = str(
            token or ""
        ).strip()

        if not token:
            raise PaymentGatewayError(
                "NexPal verify token is required.",
            )

        data = self._post(
            "/verify",
            {
                "apiKey": self.api_key,
                "token": token,
            },
        )

        try:
            code = int(
                data.get("code")
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise PaymentGatewayError(
                "NexPal returned an invalid verify code.",
            ) from exc

        return VerifyPaymentResult(
            code=code,
            message=str(
                data.get(
                    "message",
                    "",
                )
            ),
            invoice_id=str(
                data.get(
                    "invoice",
                    "",
                )
            ),
            reference_number=str(
                data.get(
                    "referenceNumber",
                    "",
                )
            ),
            masked_card_number=str(
                data.get(
                    "maskedCardNumber",
                    "",
                )
            ),
            hashed_card_number=str(
                data.get(
                    "hashedCardNumber",
                    "",
                )
            ),
            request_date=str(
                data.get(
                    "requestDate",
                    "",
                )
            ),
            amount_rial=int(
                data.get(
                    "amount",
                    0,
                )
                or 0
            ),
            description=str(
                data.get(
                    "description",
                    "",
                )
            ),
        )

    def reverse_payment(
        self,
        *,
        token: str,
    ) -> dict:
        token = str(
            token or ""
        ).strip()

        if not token:
            raise PaymentGatewayError(
                "NexPal reverse token is required.",
            )

        return self._post(
            "/reverse",
            {
                "apiKey": self.api_key,
                "token": token,
            },
        )