from __future__ import annotations

from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import Q

from .base import (
    CreatePaymentResult,
    PaymentGateway,
    PaymentGatewayError,
    TransactionResult,
    VerifyPaymentResult,
)


class ZarinPalGateway(PaymentGateway):
    """ZarinPal API v4 gateway, defaulting to the official sandbox URLs.

    Rosha stores deposit amounts in Toman. The request uses currency=IRT
    and the Toman amount. Verification sends the same numeric amount as the
    request, while normalized internal results retain the Rial equivalent.
    """

    name = "zarinpal"

    def __init__(self):
        self.merchant_id = str(
            getattr(settings, "ZARINPAL_MERCHANT_ID", "") or ""
        ).strip()
        self.base_url = str(
            getattr(
                settings,
                "ZARINPAL_BASE_URL",
                "https://sandbox.zarinpal.com/pg/v4/payment",
            )
        ).strip().rstrip("/")
        self.startpay_base_url = str(
            getattr(
                settings,
                "ZARINPAL_STARTPAY_BASE_URL",
                "https://sandbox.zarinpal.com/pg/StartPay",
            )
        ).strip().rstrip("/")
        self.callback_url = str(
            getattr(settings, "ZARINPAL_CALLBACK_URL", "") or ""
        ).strip()
        self.timeout = float(getattr(settings, "ZARINPAL_TIMEOUT", 15))

    @staticmethod
    def _error_details(payload: dict) -> tuple[int | None, str]:
        errors = payload.get("errors")
        data = payload.get("data")
        data = data if isinstance(data, dict) else {}
        code = data.get("code")
        message = data.get("message") or payload.get("message")

        if isinstance(errors, dict):
            code = errors.get("code", code)
            message = errors.get("message", message)
        elif isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                code = first.get("code", code)
                message = first.get("message", message)

        try:
            code = int(code) if code is not None else None
        except (TypeError, ValueError):
            code = None

        return code, str(message or "ZarinPal API request failed.")

    def _post(self, endpoint: str, payload: dict) -> dict:
        if not self.merchant_id:
            raise PaymentGatewayError(
                "ZarinPal merchant ID is not configured."
            )
        if not self.base_url.startswith("https://"):
            raise PaymentGatewayError(
                "ZarinPal API URL must use HTTPS."
            )

        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}.json",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=self.timeout,
                allow_redirects=False,
            )
        except requests.Timeout as exc:
            raise PaymentGatewayError(
                "ZarinPal request timed out.", retryable=True
            ) from exc
        except requests.RequestException as exc:
            raise PaymentGatewayError(
                "ZarinPal request failed.", retryable=True
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise PaymentGatewayError(
                "ZarinPal returned a non-JSON response.",
                http_status=response.status_code,
                retryable=response.status_code >= 500,
            ) from exc

        if not isinstance(data, dict):
            raise PaymentGatewayError(
                "ZarinPal returned an invalid response format.",
                http_status=response.status_code,
            )

        if not response.ok:
            code, message = self._error_details(data)
            raise PaymentGatewayError(
                message,
                code=code,
                http_status=response.status_code,
                retryable=response.status_code in {429, 500, 502, 503},
            )

        return data

    def _payment_attempt_for_token(self, token: str):
        """Resolve the server-owned attempt so verify uses its exact amount."""
        token = str(token or "").strip()
        if not token:
            raise PaymentGatewayError("ZarinPal authority is required.")

        # Import lazily to avoid loading application models during module import.
        from ..models import PaymentAttempt

        attempt = (
            PaymentAttempt.objects.filter(gateway=self.name)
            .filter(
                Q(gateway_token=token) | Q(gateway_authority=token)
            )
            .first()
        )
        if attempt is None:
            raise PaymentGatewayError(
                "No local ZarinPal payment attempt matches this authority.",
                code=-404,
            )
        return attempt

    @staticmethod
    def _amounts(amount_toman: Decimal) -> tuple[int, int]:
        try:
            amount_toman = Decimal(str(amount_toman))
        except Exception as exc:
            raise PaymentGatewayError("Invalid Toman amount.") from exc

        if not amount_toman.is_finite() or amount_toman <= 0:
            raise PaymentGatewayError("Toman amount must be positive.")
        if amount_toman != amount_toman.to_integral_value():
            raise PaymentGatewayError(
                "ZarinPal deposit amount must be a whole number of Toman."
            )

        toman = int(amount_toman)
        return toman, toman * 10

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
        if not self.callback_url:
            raise PaymentGatewayError(
                "ZarinPal callback URL is not configured."
            )
        if not self.callback_url.startswith(("https://", "http://")):
            raise PaymentGatewayError(
                "ZarinPal callback URL must be an absolute HTTP(S) URL."
            )

        toman, amount_rial = self._amounts(amount_toman)
        metadata = {"order_id": str(invoice_id)[:64]}
        if mobile:
            metadata["mobile"] = str(mobile).strip()
        if email:
            metadata["email"] = str(email).strip().lower()

        # IRT makes the hosted checkout display the amount in Toman.
        payload = {
            "merchant_id": self.merchant_id,
            "amount": toman,
            "currency": "IRT",
            "callback_url": self.callback_url,
            "description": str(description or "Rosha Toman deposit")[:500],
            "metadata": metadata,
        }
        response = self._post("request", payload)
        data = response.get("data")
        data = data if isinstance(data, dict) else {}

        try:
            code = int(data.get("code"))
        except (TypeError, ValueError) as exc:
            raise PaymentGatewayError(
                "ZarinPal request response has no valid code."
            ) from exc

        if code != 100:
            error_code, error_message = self._error_details(response)
            raise PaymentGatewayError(
                error_message,
                code=error_code if error_code is not None else code,
            )

        authority = str(data.get("authority") or "").strip()
        if not authority:
            raise PaymentGatewayError(
                "ZarinPal request response did not contain authority."
            )

        return CreatePaymentResult(
            token=authority,
            invoice_id=str(invoice_id),
            amount_rial=amount_rial,
            pay_url=f"{self.startpay_base_url}/{authority}",
            code=code,
            message=str(data.get("message") or "Success"),
        )

    def get_transaction(self, *, token: str) -> TransactionResult:
        attempt = self._payment_attempt_for_token(token)
        amount_rial = self._amounts(attempt.amount)[1]
        response = self._post(
            "inquiry",
            {"merchant_id": self.merchant_id, "authority": token},
        )
        data = response.get("data")
        data = data if isinstance(data, dict) else {}
        provider_status = str(data.get("status") or "").strip().upper()
        message = str(data.get("message") or provider_status or "Inquiry completed")

        # inquiry's code indicates request success, not payment success.
        # Only PAID/VERIFIED are eligible to proceed to verify.
        if provider_status in {"PAID", "VERIFIED"}:
            normalized_code = 100
        elif provider_status == "IN_BANK":
            normalized_code = 12
        elif provider_status == "REVERSED":
            normalized_code = -2
        elif provider_status == "FAILED":
            normalized_code = -1
        else:
            raw_code, _ = self._error_details(response)
            normalized_code = raw_code if raw_code not in (None, 100) else -1

        return TransactionResult(
            code=normalized_code,
            message=message,
            invoice_id=str(attempt.invoice_id or ""),
            amount_rial=amount_rial,
            description=provider_status,
        )

    def verify_payment(self, *, token: str) -> VerifyPaymentResult:
        attempt = self._payment_attempt_for_token(token)
        amount_toman, amount_rial = self._amounts(attempt.amount)
        response = self._post(
            "verify",
            {
                "merchant_id": self.merchant_id,
                "amount": amount_toman,
                "authority": token,
            },
        )
        data = response.get("data")
        data = data if isinstance(data, dict) else {}

        try:
            provider_code = int(data.get("code"))
        except (TypeError, ValueError):
            provider_code, _ = self._error_details(response)
            provider_code = provider_code if provider_code is not None else -1

        # Normalize ZarinPal 101 (already verified) to the existing gateway
        # interface's repeat-verification code 13 used by TestNexPalGateway.
        code = 13 if provider_code == 101 else provider_code
        verified_amount = amount_rial if provider_code in {100, 101} else 0
        message = str(data.get("message") or "")
        if provider_code == 101 and not message:
            message = "Already verified (ZarinPal code 101)"

        return VerifyPaymentResult(
            code=code,
            message=message,
            invoice_id=str(attempt.invoice_id or ""),
            reference_number=str(data.get("ref_id") or ""),
            masked_card_number=str(data.get("card_pan") or ""),
            hashed_card_number=str(data.get("card_hash") or ""),
            amount_rial=verified_amount,
            description=str(data.get("message") or ""),
        )

    def reverse_payment(self, *, token: str) -> dict:
        response = self._post(
            "reverse",
            {"merchant_id": self.merchant_id, "authority": token},
        )
        data = response.get("data")
        data = data if isinstance(data, dict) else {}
        try:
            code = int(data.get("code"))
        except (TypeError, ValueError) as exc:
            raise PaymentGatewayError(
                "ZarinPal reverse response has no valid code."
            ) from exc
        if code != 100:
            error_code, error_message = self._error_details(response)
            raise PaymentGatewayError(
                error_message,
                code=error_code if error_code is not None else code,
            )
        return data
