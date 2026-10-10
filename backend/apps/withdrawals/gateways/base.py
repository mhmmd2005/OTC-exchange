from __future__ import annotations

from dataclasses import dataclass


class PayoutGatewayError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "PAYOUT_GATEWAY_ERROR",
        retryable: bool = True,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class PayoutResult:
    success: bool
    reference: str
    code: str
    message: str


class PayoutGateway:
    def create_payout(
        self,
        *,
        request_id: str,
        amount_toman,
        iban: str,
        owner_name: str,
        description: str,
    ) -> PayoutResult:
        raise NotImplementedError