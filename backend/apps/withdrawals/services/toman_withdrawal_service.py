from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import BankAccount
from apps.assets.models import Asset
from apps.kyc.models import KycApplication
from apps.transactions.models import Transaction
from apps.wallets.models import Wallet
from apps.wallets.services import (
    InsufficientWalletBalance,
    complete_locked_wallet,
    lock_wallet,
    release_locked_wallet,
)
from ..gateways import get_payout_gateway
from ..gateways.base import PayoutGatewayError
from ..models import TomanWithdrawalAttempt

TOMAN_ASSET_SYMBOL = getattr(
    settings,
    "TOMAN_ASSET_SYMBOL",
    "IRT",
).upper()

MIN_TOMAN_WITHDRAWAL = Decimal(
    str(
        getattr(
            settings,
            "MIN_TOMAN_WITHDRAWAL",
            "50000",
        )
    )
)

TOMAN_WITHDRAWAL_FEE = Decimal(
    str(
        getattr(
            settings,
            "TOMAN_WITHDRAWAL_FEE",
            "6000",
        )
    )
)

DEFAULT_TOMAN_DAILY_WITHDRAWAL_LIMIT = Decimal(
    "500000000",
)

ESTIMATE_TTL_SECONDS = int(
    getattr(
        settings,
        "TOMAN_WITHDRAWAL_ESTIMATE_TTL_SECONDS",
        300,
    )
)


class TomanWithdrawalValidationError(Exception):
    def __init__(
            self,
            *,
            message: str,
            code: str,
            fields: dict[str, str] | None = None,
            status_code: int = 422,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.fields = fields
        self.status_code = status_code


@dataclass(frozen=True)
class WithdrawalEstimateResult:
    estimate_token: str
    estimate_version: int
    expires_at: object
    amount: Decimal
    bank_account_id: str
    fee: Decimal
    receivable: Decimal
    estimated_settlement: str


def _parse_amount(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (
            InvalidOperation,
            TypeError,
            ValueError,
    ) as exc:
        raise TomanWithdrawalValidationError(
            message="مبلغ برداشت معتبر نیست.",
            code="VALIDATION_ERROR",
            fields={
                "amount": "یک مبلغ معتبر وارد کنید.",
            },
        ) from exc

    if not amount.is_finite():
        raise TomanWithdrawalValidationError(
            message="مبلغ برداشت معتبر نیست.",
            code="VALIDATION_ERROR",
            fields={
                "amount": "یک مبلغ معتبر وارد کنید.",
            },
        )

    if amount <= 0:
        raise TomanWithdrawalValidationError(
            message="مبلغ باید بیشتر از صفر باشد.",
            code="VALIDATION_ERROR",
            fields={
                "amount": "مبلغ باید بیشتر از صفر باشد.",
            },
        )

    if amount != amount.to_integral_value():
        raise TomanWithdrawalValidationError(
            message="مبلغ برداشت باید به تومان کامل باشد.",
            code="VALIDATION_ERROR",
            fields={
                "amount": "مبلغ اعشاری قابل قبول نیست.",
            },
        )

    amount = amount.quantize(Decimal("1"))

    if amount < MIN_TOMAN_WITHDRAWAL:
        raise TomanWithdrawalValidationError(
            message="حداقل مبلغ برداشت ۵۰ هزار تومان است.",
            code="BELOW_MINIMUM",
            fields={
                "amount": "حداقل مبلغ برداشت ۵۰ هزار تومان است.",
            },
        )

    return amount


def _get_kyc(user) -> KycApplication:
    try:
        return KycApplication.objects.get(
            user=user,
        )
    except KycApplication.DoesNotExist as exc:
        raise TomanWithdrawalValidationError(
            message="ابتدا باید احراز هویت خود را تکمیل کنید.",
            code="KYC_REQUIRED",
            status_code=409,
        ) from exc


def _assert_withdrawal_eligibility(
        *,
        user,
        kyc: KycApplication,
) -> None:
    if not user.is_phone_verified:
        raise TomanWithdrawalValidationError(
            message="برای برداشت ابتدا شماره موبایل خود را تأیید کنید.",
            code="PHONE_VERIFICATION_REQUIRED",
            status_code=403,
        )

    if not kyc.both_identity_steps_approved:
        raise TomanWithdrawalValidationError(
            message="برای برداشت تومان باید احراز هویت شما تکمیل شده باشد.",
            code="KYC_REQUIRED",
            status_code=403,
        )


def _get_verified_bank_account(
        *,
        user,
        bank_account_id,
) -> BankAccount:
    try:
        account = (
            BankAccount.objects
            .select_related("bank")
            .get(
                id=str(bank_account_id).strip(),
                user=user,
                status="verified",
            )
        )
    except BankAccount.DoesNotExist as exc:
        raise TomanWithdrawalValidationError(
            message="حساب بانکی تأییدشده‌ای برای این درخواست پیدا نشد.",
            code="BANK_ACCOUNT_REQUIRED",
            fields={
                "bankAccountId": (
                    "یک حساب بانکی تأییدشده متعلق به خودتان انتخاب کنید."
                ),
            },
            status_code=409,
        ) from exc

    if not account.is_usable:
        raise TomanWithdrawalValidationError(
            message="این حساب بانکی در حال حاضر قابل استفاده نیست.",
            code="BANK_ACCOUNT_NOT_USABLE",
            status_code=409,
        )

    return account


def _get_toman_asset() -> Asset:
    try:
        return Asset.objects.get(
            symbol=TOMAN_ASSET_SYMBOL,
            is_active=True,
        )
    except Asset.DoesNotExist as exc:
        raise RuntimeError(
            f"Active toman asset '{TOMAN_ASSET_SYMBOL}' does not exist."
        ) from exc


def _get_wallet(
        *,
        user_id,
        asset_id,
) -> Wallet:
    try:
        return (
            Wallet.objects
            .select_for_update()
            .get(
                user_id=user_id,
                asset_id=asset_id,
            )
        )
    except Wallet.DoesNotExist as exc:
        raise TomanWithdrawalValidationError(
            message="کیف پول تومان شما پیدا نشد.",
            code="WALLET_NOT_FOUND",
            status_code=409,
        ) from exc


def _get_daily_limit() -> Decimal:
    return _get_toman_daily_withdrawal_limit()


def get_used_toman_withdrawal_today(
        *,
        user,
) -> Decimal:
    now = timezone.localtime()

    day_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    total = (
        TomanWithdrawalAttempt.objects
        .filter(
            user=user,
            created_at__gte=day_start,
            created_at__lt=now,
            status__in={
                TomanWithdrawalAttempt.Status.PROCESSING,
                TomanWithdrawalAttempt.Status.SUCCEEDED,
            },
        )
        .aggregate(
            total=Sum("amount"),
        )
    )["total"]

    return total or Decimal("0")


def _get_toman_daily_withdrawal_limit() -> Decimal:
    raw_limit = getattr(
        settings,
        "TOMAN_DAILY_WITHDRAWAL_LIMIT",
        DEFAULT_TOMAN_DAILY_WITHDRAWAL_LIMIT,
    )

    try:
        limit = Decimal(str(raw_limit))
    except (
            InvalidOperation,
            TypeError,
            ValueError,
    ) as exc:
        raise RuntimeError(
            "TOMAN_DAILY_WITHDRAWAL_LIMIT is invalid.",
        ) from exc

    if limit < 0:
        raise RuntimeError(
            "TOMAN_DAILY_WITHDRAWAL_LIMIT cannot be negative.",
        )

    return limit


def get_toman_withdrawal_limit_data(
        *,
        user,
) -> dict[str, Decimal]:
    daily_limit = _get_toman_daily_withdrawal_limit()

    used_today = get_used_toman_withdrawal_today(
        user=user,
    )

    remaining = daily_limit - used_today

    if remaining < 0:
        remaining = Decimal("0")

    return {
        "daily": daily_limit,
        "used": used_today,
        "remaining": remaining,
    }


def _get_remaining_daily_limit(
        *,
        user,
) -> Decimal:
    remaining = (
            _get_daily_limit()
            - get_used_toman_withdrawal_today(
        user=user,
    )
    )

    return max(
        remaining,
        Decimal("0"),
    )


def _make_estimate_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_estimate_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _normalize_idempotency_key(
        *,
        user,
        client_key: str,
) -> str:
    client_key = str(
        client_key or "",
    ).strip()

    if not client_key:
        raise TomanWithdrawalValidationError(
            message="شناسه یکتای برداشت ارسال نشده است.",
            code="IDEMPOTENCY_KEY_REQUIRED",
            fields={
                "idempotencyKey": (
                    "Idempotency-Key الزامی است."
                ),
            },
            status_code=400,
        )

    if len(client_key) < 16:
        raise TomanWithdrawalValidationError(
            message="شناسه یکتای برداشت معتبر نیست.",
            code="VALIDATION_ERROR",
            fields={
                "idempotencyKey": (
                    "حداقل طول Idempotency-Key برابر ۱۶ کاراکتر است."
                ),
            },
            status_code=400,
        )

    if len(client_key) > 128:
        raise TomanWithdrawalValidationError(
            message="شناسه یکتای برداشت معتبر نیست.",
            code="VALIDATION_ERROR",
            fields={
                "idempotencyKey": (
                    "حداکثر طول Idempotency-Key برابر ۱۲۸ کاراکتر است."
                ),
            },
            status_code=400,
        )

    if not re.fullmatch(
            r"[A-Za-z0-9_-]{16,128}",
            client_key,
    ):
        raise TomanWithdrawalValidationError(
            message="شناسه یکتای برداشت معتبر نیست.",
            code="VALIDATION_ERROR",
            fields={
                "idempotencyKey": (
                    "Idempotency-Key فقط می‌تواند شامل حروف، "
                    "اعداد، _ و - باشد."
                ),
            },
            status_code=400,
        )

    digest = hashlib.sha256(
        client_key.encode("utf-8")
    ).hexdigest()

    return (
        f"toman-withdrawal:"
        f"{user.pk}:"
        f"{digest}"
    )


@transaction.atomic
def create_toman_withdrawal_estimate(
        *,
        user,
        amount,
        bank_account_id,
) -> WithdrawalEstimateResult:
    amount = _parse_amount(amount)

    kyc = _get_kyc(user)

    _assert_withdrawal_eligibility(
        user=user,
        kyc=kyc,
    )

    bank_account = _get_verified_bank_account(
        user=user,
        bank_account_id=bank_account_id,
    )

    asset = _get_toman_asset()

    wallet = _get_wallet(
        user_id=user.pk,
        asset_id=asset.pk,
    )

    if wallet.available_balance < amount:
        raise TomanWithdrawalValidationError(
            message="موجودی قابل برداشت شما کافی نیست.",
            code="INSUFFICIENT_BALANCE",
            fields={
                "amount": "موجودی قابل برداشت کافی نیست.",
            },
            status_code=409,
        )

    remaining = _get_remaining_daily_limit(
        user=user,
    )

    if amount > remaining:
        raise TomanWithdrawalValidationError(
            message="مبلغ از سقف باقی‌مانده برداشت امروز بیشتر است.",
            code="DAILY_LIMIT_EXCEEDED",
            fields={
                "amount": (
                    "مبلغ از سقف باقی‌مانده برداشت امروز بیشتر است."
                ),
            },
            status_code=409,
        )

    fee = min(
        TOMAN_WITHDRAWAL_FEE,
        amount,
    )

    receivable = amount - fee

    token = _make_estimate_token()
    expires_at = (
            timezone.now()
            + timedelta(
        seconds=ESTIMATE_TTL_SECONDS,
    )
    )

    TomanWithdrawalAttempt.objects.create(
        user=user,
        bank_account=bank_account,
        amount=amount,
        fee=fee,
        receivable=receivable,
        estimate_token_hash=_hash_estimate_token(token),
        estimate_version=1,
        status=TomanWithdrawalAttempt.Status.ESTIMATED,
        expires_at=expires_at,
    )

    return WithdrawalEstimateResult(
        estimate_token=token,
        estimate_version=1,
        expires_at=expires_at,
        amount=amount,
        bank_account_id=str(bank_account.pk),
        fee=fee,
        receivable=receivable,
        estimated_settlement="اولین چرخه پایای روز کاری بعد",
    )


@transaction.atomic
def _lock_withdrawal(
        *,
        user,
        attempt: TomanWithdrawalAttempt,
        idempotency_key: str,
) -> Transaction:
    asset = _get_toman_asset()

    wallet = _get_wallet(
        user_id=user.pk,
        asset_id=asset.pk,
    )

    remaining = _get_remaining_daily_limit(
        user=user,
    )

    if attempt.amount > remaining:
        raise TomanWithdrawalValidationError(
            message="سقف برداشت روزانه در زمان ثبت درخواست کافی نیست.",
            code="DAILY_LIMIT_EXCEEDED",
            status_code=409,
        )

    try:
        lock_wallet(
            user_id=user.pk,
            asset_id=asset.pk,
            amount=attempt.amount,
        )
    except InsufficientWalletBalance as exc:
        raise TomanWithdrawalValidationError(
            message="موجودی قابل برداشت شما کافی نیست.",
            code="INSUFFICIENT_BALANCE",
            status_code=409,
        ) from exc

    now = timezone.now()

    withdrawal_transaction = Transaction.objects.create(
        user=user,
        asset=asset,
        transaction_type="toman_withdrawal",
        amount=attempt.amount,
        toman_amount=attempt.receivable,
        fee=attempt.fee,
        bank_account_id=str(attempt.bank_account_id),
        idempotency_key=idempotency_key,
        title="برداشت تومان",
        description=(
            "درخواست برداشت تومان - "
            f"حساب بانکی {attempt.bank_account_id}"
        ),
        status="processing",
    )

    attempt.status = (
        TomanWithdrawalAttempt.Status.PROCESSING
    )

    attempt.idempotency_key = idempotency_key
    attempt.transaction = withdrawal_transaction

    attempt.save(
        update_fields=[
            "status",
            "idempotency_key",
            "transaction",
            "updated_at",
        ],
    )

    # Keep the variable intentionally referenced so this critical
    # locked row remains part of the same transaction boundary.
    _ = wallet
    _ = now

    return withdrawal_transaction


@transaction.atomic
def _mark_withdrawal_success(
        *,
        attempt_id,
        provider_reference: str,
        provider_code: str,
        provider_message: str,
) -> Transaction:
    attempt = (
        TomanWithdrawalAttempt.objects
        .select_for_update()
        .select_related(
            "user",
            "bank_account",
            "transaction",
        )
        .get(
            pk=attempt_id,
        )
    )

    if (
            attempt.status
            == TomanWithdrawalAttempt.Status.SUCCEEDED
    ):
        if attempt.transaction_id:
            return attempt.transaction

        raise RuntimeError(
            "Succeeded withdrawal has no transaction.",
        )

    transaction_record = attempt.transaction

    if transaction_record is None:
        raise RuntimeError(
            "Withdrawal attempt has no transaction.",
        )

    if transaction_record.status == "completed":
        attempt.status = (
            TomanWithdrawalAttempt.Status.SUCCEEDED
        )
        attempt.provider_reference = provider_reference
        attempt.provider_code = provider_code
        attempt.provider_message = provider_message
        attempt.completed_at = (
                transaction_record.completed_at
                or timezone.now()
        )

        attempt.save(
            update_fields=[
                "status",
                "provider_reference",
                "provider_code",
                "provider_message",
                "completed_at",
                "updated_at",
            ],
        )

        return transaction_record

    complete_locked_wallet(
        user_id=attempt.user_id,
        asset_id=transaction_record.asset_id,
        amount=attempt.amount,
    )

    now = timezone.now()

    transaction_record.status = "completed"
    transaction_record.completed_at = now
    transaction_record.txid = provider_reference
    transaction_record.save(
        update_fields=[
            "status",
            "completed_at",
            "txid",
            "updated_at",
        ],
    )

    attempt.status = (
        TomanWithdrawalAttempt.Status.SUCCEEDED
    )
    attempt.provider_reference = provider_reference
    attempt.provider_code = provider_code
    attempt.provider_message = provider_message
    attempt.completed_at = now

    attempt.save(
        update_fields=[
            "status",
            "provider_reference",
            "provider_code",
            "provider_message",
            "completed_at",
            "updated_at",
        ],
    )

    return transaction_record


@transaction.atomic
def _mark_withdrawal_failure(
        *,
        attempt_id,
        provider_code: str,
        provider_message: str,
) -> Transaction:
    attempt = (
        TomanWithdrawalAttempt.objects
        .select_for_update()
        .select_related(
            "transaction",
        )
        .get(
            pk=attempt_id,
        )
    )

    if (
            attempt.status
            == TomanWithdrawalAttempt.Status.SUCCEEDED
    ):
        return attempt.transaction

    transaction_record = attempt.transaction

    if transaction_record is not None:
        if transaction_record.status != "failed":
            release_locked_wallet(
                user_id=attempt.user_id,
                asset_id=transaction_record.asset_id,
                amount=attempt.amount,
            )

            transaction_record.status = "failed"
            transaction_record.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

    attempt.status = (
        TomanWithdrawalAttempt.Status.FAILED
    )
    attempt.provider_code = provider_code
    attempt.provider_message = provider_message
    attempt.failed_at = timezone.now()

    attempt.save(
        update_fields=[
            "status",
            "provider_code",
            "provider_message",
            "failed_at",
            "updated_at",
        ],
    )

    return transaction_record


def create_toman_withdrawal(
        *,
        user,
        estimate_token: str,
        estimate_version: int,
        idempotency_key: str,
) -> Transaction:
    estimate_token = str(
        estimate_token or "",
    ).strip()

    if not estimate_token:
        raise TomanWithdrawalValidationError(
            message="توکن برآورد برداشت ارسال نشده است.",
            code="ESTIMATE_REQUIRED",
            status_code=400,
        )

    try:
        estimate_version = int(
            estimate_version
        )
    except (
            TypeError,
            ValueError,
    ) as exc:
        raise TomanWithdrawalValidationError(
            message="نسخه برآورد برداشت معتبر نیست.",
            code="ESTIMATE_INVALID",
            status_code=400,
        ) from exc

    normalized_key = _normalize_idempotency_key(
        user=user,
        client_key=idempotency_key,
    )

    with transaction.atomic():
        existing = (
            TomanWithdrawalAttempt.objects
            .select_for_update()
            .select_related("transaction")
            .filter(
                user=user,
                idempotency_key=normalized_key,
            )
            .first()
        )

        if existing is not None:
            if existing.transaction_id:
                return existing.transaction

        estimate = (
            TomanWithdrawalAttempt.objects
            .select_for_update()
            .select_related(
                "bank_account",
                "user",
            )
            .filter(
                user=user,
                estimate_token_hash=_hash_estimate_token(
                    estimate_token
                ),
            )
            .first()
        )

        if estimate is None:
            raise TomanWithdrawalValidationError(
                message="برآورد برداشت معتبر نیست.",
                code="ESTIMATE_INVALID",
                status_code=409,
            )

        if estimate.estimate_version != estimate_version:
            raise TomanWithdrawalValidationError(
                message="نسخه برآورد برداشت منقضی یا نامعتبر است.",
                code="ESTIMATE_VERSION_INVALID",
                status_code=409,
            )

        if estimate.status != (
                TomanWithdrawalAttempt.Status.ESTIMATED
        ):
            raise TomanWithdrawalValidationError(
                message="این برآورد قبلاً استفاده شده است.",
                code="ESTIMATE_ALREADY_USED",
                status_code=409,
            )

        if (
                estimate.expires_at
                and estimate.expires_at <= timezone.now()
        ):
            estimate.status = (
                TomanWithdrawalAttempt.Status.EXPIRED
            )
            estimate.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

            raise TomanWithdrawalValidationError(
                message="مهلت برآورد برداشت به پایان رسیده است.",
                code="ESTIMATE_EXPIRED",
                status_code=410,
            )

        _get_verified_bank_account(
            user=user,
            bank_account_id=estimate.bank_account_id,
        )

        withdrawal_transaction = _lock_withdrawal(
            user=user,
            attempt=estimate,
            idempotency_key=normalized_key,
        )

        attempt_id = estimate.pk

    gateway = get_payout_gateway()

    try:
        payout_result = gateway.create_payout(
            request_id=normalized_key,
            amount_toman=estimate.receivable,
            iban=estimate.bank_account.iban,
            owner_name=estimate.bank_account.owner_name,
            description=(
                f"برداشت تومان - "
                f"{withdrawal_transaction.reference_number}"
            ),
        )
    except PayoutGatewayError as exc:
        _mark_withdrawal_failure(
            attempt_id=attempt_id,
            provider_code=str(exc.code),
            provider_message=exc.message,
        )

        raise TomanWithdrawalValidationError(
            message=(
                "در حال حاضر انتقال وجه انجام نشد."
            ),
            code="PAYOUT_GATEWAY_UNAVAILABLE",
            status_code=503,
        ) from exc

    if not payout_result.success:
        _mark_withdrawal_failure(
            attempt_id=attempt_id,
            provider_code=payout_result.code,
            provider_message=payout_result.message,
        )

        raise TomanWithdrawalValidationError(
            message=payout_result.message
                    or "انتقال وجه انجام نشد.",
            code="PAYOUT_FAILED",
            status_code=409,
        )

    return _mark_withdrawal_success(
        attempt_id=attempt_id,
        provider_reference=payout_result.reference,
        provider_code=payout_result.code,
        provider_message=payout_result.message,
    )
