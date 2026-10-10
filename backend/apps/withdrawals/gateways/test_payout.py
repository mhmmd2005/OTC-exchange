from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import ClassVar

from .base import (
    PayoutGateway,
    PayoutGatewayError,
    PayoutResult,
)


@dataclass
class TestPayoutGateway(PayoutGateway):
    _payouts: ClassVar[dict[str, PayoutResult]] = {}

    def create_payout(
        self,
        *,
        request_id: str,
        amount_toman,
        iban: str,
        owner_name: str,
        description: str,
    ) -> PayoutResult:
        request_id = str(request_id).strip()

        if not request_id:
            raise PayoutGatewayError(
                message="شناسه درخواست تسویه موجود نیست.",
                code="REQUEST_ID_REQUIRED",
                retryable=False,
            )

        existing = self._payouts.get(request_id)

        if existing is not None:
            return existing

        reference = (
            "TP-"
            + uuid.uuid4().hex[:20].upper()
        )

        result = PayoutResult(
            success=True,
            reference=reference,
            code="100",
            message="تسویه آزمایشی با موفقیت شبیه‌سازی شد.",
        )

        self._payouts[request_id] = result

        return result