from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


class PaymentGatewayError(Exception):
    """
    Base exception for all payment gateway errors.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        http_status: int | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)

        self.message = message
        self.code = code
        self.http_status = http_status
        self.retryable = retryable


@dataclass(frozen=True)
class CreatePaymentResult:
    """
    Normalized result returned by a gateway
    after creating a payment.
    """

    token: str
    invoice_id: str
    amount_rial: int
    pay_url: str
    code: int
    message: str


@dataclass(frozen=True)
class TransactionResult:
    """
    Normalized result returned by a gateway
    transaction inquiry.
    """

    code: int
    message: str
    invoice_id: str = ""
    reference_number: str = ""
    masked_card_number: str = ""
    hashed_card_number: str = ""
    request_date: str = ""
    amount_rial: int = 0
    description: str = ""


@dataclass(frozen=True)
class VerifyPaymentResult:
    """
    Normalized result returned by a gateway
    after payment verification.
    """

    code: int
    message: str
    invoice_id: str = ""
    reference_number: str = ""
    masked_card_number: str = ""
    hashed_card_number: str = ""
    request_date: str = ""
    amount_rial: int = 0
    description: str = ""


class PaymentGateway(ABC):
    """
    Common interface for all payment gateways.

    Business logic must depend on this interface,
    not on a specific provider such as NexPal.
    """

    name: str

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def get_transaction(
        self,
        *,
        token: str,
    ) -> TransactionResult:
        raise NotImplementedError

    @abstractmethod
    def verify_payment(
        self,
        *,
        token: str,
    ) -> VerifyPaymentResult:
        raise NotImplementedError

    @abstractmethod
    def reverse_payment(
        self,
        *,
        token: str,
    ) -> dict:
        raise NotImplementedError