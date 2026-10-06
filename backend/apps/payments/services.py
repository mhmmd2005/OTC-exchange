from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import BankAccount
from apps.assets.models import Asset
from apps.kyc.models import KycApplication
from apps.transactions.models import Transaction
from apps.wallets.services import credit_wallet
from .gateways import get_payment_gateway
from .gateways.base import PaymentGatewayError
from .models import PaymentAttempt

TOMAN_ASSET_SYMBOL = getattr(
    settings,
    "TOMAN_ASSET_SYMBOL",
    "IRT",
).upper()

DEFAULT_TOMAN_DAILY_DEPOSIT_LIMIT = Decimal(
    "500000000",
)

MIN_TOMAN_DEPOSIT = Decimal(
    "100000",
)

PAYMENT_ATTEMPT_EXPIRES_MINUTES = 10

UserModel = get_user_model()


@dataclass(frozen=True)
class TomanDepositValidationError(Exception):
    message: str
    code: str
    fields: dict[str, str] | None = None
    status_code: int = 422


def _get_daily_toman_deposit_limit() -> Decimal:
    raw_limit = getattr(
        settings,
        "TOMAN_DAILY_DEPOSIT_LIMIT",
        DEFAULT_TOMAN_DAILY_DEPOSIT_LIMIT,
    )

    try:
        limit = Decimal(str(raw_limit))
    except (
            InvalidOperation,
            TypeError,
            ValueError,
    ) as exc:
        raise RuntimeError(
            "TOMAN_DAILY_DEPOSIT_LIMIT is invalid.",
        ) from exc

    if limit < 0:
        raise RuntimeError(
            "TOMAN_DAILY_DEPOSIT_LIMIT cannot be negative.",
        )

    return limit


def get_toman_deposit_limit_data(
        *,
        user,
) -> dict[str, Decimal]:
    daily_limit = _get_daily_toman_deposit_limit()

    used_today = get_used_toman_deposit_today(
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


def _parse_amount(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (
            InvalidOperation,
            TypeError,
            ValueError,
    ) as exc:
        raise TomanDepositValidationError(
            message="مبلغ واریز معتبر نیست.",
            code="VALIDATION_ERROR",
            fields={
                "amount": "یک مبلغ معتبر وارد کنید.",
            },
        ) from exc

    if not amount.is_finite():
        raise TomanDepositValidationError(
            message="مبلغ واریز معتبر نیست.",
            code="VALIDATION_ERROR",
            fields={
                "amount": "یک مبلغ معتبر وارد کنید.",
            },
        )

    if amount <= 0:
        raise TomanDepositValidationError(
            message="مبلغ باید بیشتر از صفر باشد.",
            code="VALIDATION_ERROR",
            fields={
                "amount": "یک مبلغ معتبر وارد کنید.",
            },
        )

    if amount != amount.to_integral_value():
        raise TomanDepositValidationError(
            message="مبلغ واریز باید به تومان کامل باشد.",
            code="VALIDATION_ERROR",
            fields={
                "amount": "مبلغ اعشاری قابل قبول نیست.",
            },
        )

    amount = amount.quantize(
        Decimal("1"),
    )

    if amount < MIN_TOMAN_DEPOSIT:
        raise TomanDepositValidationError(
            message="حداقل مبلغ واریز ۱۰۰ هزار تومان است.",
            code="BELOW_MINIMUM",
            fields={
                "amount": "حداقل مبلغ واریز ۱۰۰ هزار تومان است.",
            },
        )

    return amount


def _parse_rial_amount(value) -> int:
    try:
        amount = int(value)
    except (
            TypeError,
            ValueError,
    ) as exc:
        raise TomanDepositValidationError(
            message="مبلغ پرداخت دریافتی معتبر نیست.",
            code="PAYMENT_AMOUNT_INVALID",
            status_code=400,
        ) from exc

    if amount <= 0:
        raise TomanDepositValidationError(
            message="مبلغ پرداخت دریافتی معتبر نیست.",
            code="PAYMENT_AMOUNT_INVALID",
            status_code=400,
        )

    return amount


def _is_successful_callback_status(value) -> bool:
    if value is True:
        return True

    if value is False or value is None:
        return False

    normalized = (
        str(value)
        .strip()
        .lower()
    )

    return normalized in {
        "true",
        "1",
        "success",
        "successful",
        "paid",
        "ok",
    }


def _normalize_idempotency_key(
        *,
        user,
        client_key: str,
) -> str:
    client_key = str(
        client_key or "",
    ).strip()

    if not client_key:
        raise TomanDepositValidationError(
            message=(
                "شناسه یکتای درخواست پرداخت "
                "ارسال نشده است."
            ),
            code="IDEMPOTENCY_KEY_REQUIRED",
            fields={
                "idempotencyKey": (
                    "Idempotency-Key الزامی است."
                ),
            },
            status_code=400,
        )

    if len(client_key) > 128:
        raise TomanDepositValidationError(
            message=(
                "شناسه یکتای درخواست پرداخت معتبر نیست."
            ),
            code="VALIDATION_ERROR",
            fields={
                "idempotencyKey": (
                    "حداکثر طول Idempotency-Key "
                    "۱۲۸ کاراکتر است."
                ),
            },
            status_code=400,
        )

    if re.search(
            r"[\x00-\x1f\x7f]",
            client_key,
    ):
        raise TomanDepositValidationError(
            message=(
                "شناسه یکتای درخواست پرداخت معتبر نیست."
            ),
            code="VALIDATION_ERROR",
            fields={
                "idempotencyKey": (
                    "Idempotency-Key دارای "
                    "کاراکتر نامعتبر است."
                ),
            },
            status_code=400,
        )

    digest = hashlib.sha256(
        client_key.encode("utf-8"),
    ).hexdigest()

    return (
        f"toman-deposit:"
        f"{user.pk}:"
        f"{digest}"
    )


def _get_verified_bank_account(
        *,
        user,
        bank_account_id: str,
) -> BankAccount:
    bank_account_id = str(
        bank_account_id or "",
    ).strip()

    if not bank_account_id:
        raise TomanDepositValidationError(
            message=(
                "برای واریز، یک کارت بانکی "
                "تأییدشده انتخاب کنید."
            ),
            code="BANK_ACCOUNT_REQUIRED",
            fields={
                "bankAccountId": (
                    "یک کارت بانکی تأییدشده "
                    "انتخاب کنید."
                ),
            },
            status_code=409,
        )

    try:
        return (
            BankAccount.objects
            .select_related("bank")
            .get(
                id=bank_account_id,
                user=user,
                status="verified",
            )
        )
    except BankAccount.DoesNotExist as exc:
        raise TomanDepositValidationError(
            message=(
                "برای واریز، یک کارت بانکی "
                "تأییدشده انتخاب کنید."
            ),
            code="BANK_ACCOUNT_REQUIRED",
            fields={
                "bankAccountId": (
                    "یک کارت بانکی تأییدشده "
                    "انتخاب کنید."
                ),
            },
            status_code=409,
        ) from exc


def _get_kyc(
        user,
) -> KycApplication:
    try:
        return KycApplication.objects.get(
            user=user,
        )
    except KycApplication.DoesNotExist as exc:
        raise TomanDepositValidationError(
            message=(
                "ابتدا باید احراز هویت "
                "خود را تکمیل کنید."
            ),
            code="KYC_REQUIRED",
            status_code=409,
        ) from exc


def _assert_deposit_eligibility(
        *,
        user,
        kyc: KycApplication,
) -> None:
    if not user.is_phone_verified:
        raise TomanDepositValidationError(
            message=(
                "برای واریز، ابتدا شماره موبایل "
                "خود را تأیید کنید."
            ),
            code="PHONE_VERIFICATION_REQUIRED",
            status_code=403,
        )

    if not kyc.both_identity_steps_approved:
        raise TomanDepositValidationError(
            message=(
                "برای واریز تومان باید "
                "احراز هویت خود را تکمیل کنید."
            ),
            code="KYC_REQUIRED",
            status_code=403,
        )


def _get_toman_asset() -> Asset:
    try:
        return Asset.objects.get(
            symbol=TOMAN_ASSET_SYMBOL,
            is_active=True,
        )
    except Asset.DoesNotExist as exc:
        raise RuntimeError(
            f"Active toman asset "
            f"'{TOMAN_ASSET_SYMBOL}' "
            "does not exist.",
        ) from exc


def get_used_toman_deposit_today(
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

    used = (
        Transaction.objects
        .filter(
            user=user,
            asset__symbol=TOMAN_ASSET_SYMBOL,
            transaction_type="toman_deposit",
            status="completed",
            created_at__gte=day_start,
            created_at__lt=now,
        )
        .aggregate(
            total=Sum("amount"),
        )
    )["total"]

    return used or Decimal("0")


def _calculate_remaining_daily_limit(
        *,
        user,
) -> Decimal:
    daily_limit = (
        _get_daily_toman_deposit_limit()
    )

    used_today = (
        get_used_toman_deposit_today(
            user=user,
        )
    )

    remaining = (
            daily_limit - used_today
    )

    return max(
        remaining,
        Decimal("0"),
    )


def _build_invoice_id() -> str:
    return (
            "TD-"
            + uuid.uuid4().hex
    )


def _get_or_create_payment_attempt(
        *,
        user,
        amount: Decimal,
        bank_account: BankAccount,
        idempotency_key: str,
) -> PaymentAttempt:
    invoice_id = _build_invoice_id()

    with transaction.atomic():
        existing = (
            PaymentAttempt.objects
            .select_for_update()
            .filter(
                idempotency_key=idempotency_key,
            )
            .first()
        )

        if existing:
            if existing.user_id != user.pk:
                raise TomanDepositValidationError(
                    message=(
                        "درخواست پرداخت معتبر نیست."
                    ),
                    code="IDEMPOTENCY_CONFLICT",
                    status_code=409,
                )

            if existing.amount != amount:
                raise TomanDepositValidationError(
                    message=(
                        "درخواست با این "
                        "Idempotency-Key قبلاً "
                        "با مبلغ دیگری ثبت شده است."
                    ),
                    code="IDEMPOTENCY_CONFLICT",
                    status_code=409,
                )

            if existing.bank_account_id != bank_account.id:
                raise TomanDepositValidationError(
                    message=(
                        "درخواست با این "
                        "Idempotency-Key قبلاً "
                        "با حساب بانکی دیگری ثبت شده است."
                    ),
                    code="IDEMPOTENCY_CONFLICT",
                    status_code=409,
                )

            return existing

        try:
            payment_attempt = (
                PaymentAttempt.objects.create(
                    user=user,
                    bank_account=bank_account,
                    amount=amount,
                    currency="IRT",
                    gateway="nexpal",
                    gateway_authority="",
                    gateway_reference=invoice_id,
                    gateway_token="",
                    invoice_id=invoice_id,
                    gateway_code="",
                    gateway_message="",
                    payment_url="",
                    idempotency_key=idempotency_key,
                    status="created",
                    expires_at=(
                            timezone.now()
                            + timedelta(
                        minutes=(
                            PAYMENT_ATTEMPT_EXPIRES_MINUTES
                        )
                    )
                    ),
                )
            )
        except Exception:
            existing = (
                PaymentAttempt.objects
                .select_for_update()
                .filter(
                    idempotency_key=idempotency_key,
                )
                .first()
            )

            if existing is None:
                raise

            if existing.user_id != user.pk:
                raise TomanDepositValidationError(
                    message="درخواست پرداخت معتبر نیست.",
                    code="IDEMPOTENCY_CONFLICT",
                    status_code=409,
                )

            if existing.amount != amount:
                raise TomanDepositValidationError(
                    message=(
                        "درخواست با این "
                        "Idempotency-Key قبلاً "
                        "با مبلغ دیگری ثبت شده است."
                    ),
                    code="IDEMPOTENCY_CONFLICT",
                    status_code=409,
                )

            if existing.bank_account_id != bank_account.id:
                raise TomanDepositValidationError(
                    message=(
                        "درخواست با این "
                        "Idempotency-Key قبلاً "
                        "با حساب بانکی دیگری ثبت شده است."
                    ),
                    code="IDEMPOTENCY_CONFLICT",
                    status_code=409,
                )

            payment_attempt = existing

        return payment_attempt


def _mark_gateway_failure(
        *,
        payment_attempt: PaymentAttempt,
        gateway_error: PaymentGatewayError,
) -> None:
    payment_attempt.status = "failed"

    payment_attempt.failed_at = timezone.now()

    payment_attempt.gateway_code = (
        str(gateway_error.code)
        if gateway_error.code is not None
        else ""
    )

    payment_attempt.gateway_message = (
        gateway_error.message
    )

    payment_attempt.save(
        update_fields=[
            "status",
            "failed_at",
            "gateway_code",
            "gateway_message",
            "updated_at",
        ],
    )


def _mark_payment_attempt_failed(
        *,
        payment_attempt_id,
        code: str,
        message: str,
) -> None:
    with transaction.atomic():
        locked_attempt = (
            PaymentAttempt.objects
            .select_for_update()
            .get(
                pk=payment_attempt_id,
            )
        )

        if locked_attempt.status == "succeeded":
            return

        locked_attempt.status = "failed"
        locked_attempt.failed_at = timezone.now()
        locked_attempt.gateway_code = str(code)
        locked_attempt.gateway_message = message

        locked_attempt.save(
            update_fields=[
                "status",
                "failed_at",
                "gateway_code",
                "gateway_message",
                "updated_at",
            ],
        )


def _get_attempt_invoice_id(
        payment_attempt: PaymentAttempt,
) -> str:
    return (
        str(
            payment_attempt.invoice_id
            or payment_attempt.gateway_reference
            or ""
        )
        .strip()
    )


def _get_attempt_gateway_token(
        payment_attempt: PaymentAttempt,
) -> str:
    return (
        str(
            payment_attempt.gateway_token
            or payment_attempt.gateway_authority
            or ""
        )
        .strip()
    )


def start_toman_deposit_payment(
        *,
        user,
        amount,
        bank_account_id: str,
        idempotency_key: str,
) -> PaymentAttempt:
    amount = _parse_amount(
        amount,
    )

    normalized_key = (
        _normalize_idempotency_key(
            user=user,
            client_key=idempotency_key,
        )
    )

    kyc = _get_kyc(
        user,
    )

    _assert_deposit_eligibility(
        user=user,
        kyc=kyc,
    )

    bank_account = (
        _get_verified_bank_account(
            user=user,
            bank_account_id=bank_account_id,
        )
    )

    payment_attempt = (
        _get_or_create_payment_attempt(
            user=user,
            amount=amount,
            bank_account=bank_account,
            idempotency_key=normalized_key,
        )
    )

    now = timezone.now()

    if (
            payment_attempt.expires_at
            and payment_attempt.expires_at <= now
            and payment_attempt.status
            not in {
        "succeeded",
        "failed",
        "cancelled",
        "expired",
    }
    ):
        with transaction.atomic():
            locked_attempt = (
                PaymentAttempt.objects
                .select_for_update()
                .get(
                    pk=payment_attempt.pk,
                )
            )

            if (
                    locked_attempt.expires_at
                    and locked_attempt.expires_at <= timezone.now()
                    and locked_attempt.status
                    not in {
                "succeeded",
                "failed",
                "cancelled",
                "expired",
            }
            ):
                locked_attempt.status = "expired"
                locked_attempt.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ],
                )

            payment_attempt = (
                locked_attempt
            )

    if payment_attempt.status == "redirect_ready":
        return payment_attempt

    if payment_attempt.status == "succeeded":
        return payment_attempt

    if payment_attempt.status in {
        "cancelled",
        "expired",
    }:
        raise TomanDepositValidationError(
            message=(
                "این درخواست پرداخت دیگر قابل استفاده نیست. "
                "لطفاً یک درخواست جدید ایجاد کنید."
            ),
            code="PAYMENT_ATTEMPT_NOT_REUSABLE",
            status_code=409,
        )

    if payment_attempt.status in {
        "callback_received",
        "verifying",
    }:
        return payment_attempt

    if payment_attempt.status == "created":
        remaining = (
            _calculate_remaining_daily_limit(
                user=user,
            )
        )

        if amount > remaining:
            raise TomanDepositValidationError(
                message=(
                    "مبلغ از سقف باقی‌مانده "
                    "واریز امروز بیشتر است."
                ),
                code="DAILY_LIMIT_EXCEEDED",
                fields={
                    "amount": (
                        "مبلغ از سقف باقی‌مانده "
                        "واریز امروز بیشتر است."
                    ),
                },
                status_code=409,
            )

        _get_toman_asset()

    gateway = get_payment_gateway()

    mobile = str(
        getattr(
            user,
            "phone_number",
            "",
        )
        or ""
    ).strip()

    email = str(
        getattr(
            user,
            "email",
            "",
        )
        or ""
    ).strip()

    national_code = str(
        getattr(
            kyc,
            "national_id",
            "",
        )
        or ""
    ).strip()

    invoice_id = _get_attempt_invoice_id(
        payment_attempt,
    )

    if not invoice_id:
        raise RuntimeError(
            "PaymentAttempt invoice id is missing.",
        )

    try:
        result = gateway.create_payment(
            idempotency_key=(
                payment_attempt.idempotency_key
            ),
            invoice_id=invoice_id,
            amount_toman=(
                payment_attempt.amount
            ),
            description=(
                f"واریز تومان - "
                f"{invoice_id}"
            ),
            mobile=mobile,
            email=email,
            national_code=national_code,
        )
    except PaymentGatewayError as exc:
        with transaction.atomic():
            locked_attempt = (
                PaymentAttempt.objects
                .select_for_update()
                .get(
                    pk=payment_attempt.pk,
                )
            )

            _mark_gateway_failure(
                payment_attempt=locked_attempt,
                gateway_error=exc,
            )

        raise TomanDepositValidationError(
            message=(
                "در حال حاضر ایجاد پرداخت "
                "امکان‌پذیر نیست. لطفاً دوباره تلاش کنید."
            ),
            code="PAYMENT_GATEWAY_UNAVAILABLE",
            status_code=503,
        ) from exc

    with transaction.atomic():
        locked_attempt = (
            PaymentAttempt.objects
            .select_for_update()
            .get(
                pk=payment_attempt.pk,
            )
        )

        locked_attempt.gateway = "nexpal"

        locked_attempt.gateway_token = (
            result.token
        )

        locked_attempt.invoice_id = (
            result.invoice_id
        )

        # Keep the older fields synchronized
        # for backward compatibility.
        locked_attempt.gateway_authority = (
            result.token
        )

        locked_attempt.gateway_reference = (
            result.invoice_id
        )

        locked_attempt.gateway_code = (
            str(result.code)
        )

        locked_attempt.gateway_message = (
            result.message
        )

        locked_attempt.payment_url = (
            result.pay_url
        )

        locked_attempt.status = (
            "redirect_ready"
        )

        locked_attempt.failed_at = None

        locked_attempt.save(
            update_fields=[
                "gateway",
                "gateway_token",
                "invoice_id",
                "gateway_authority",
                "gateway_reference",
                "gateway_code",
                "gateway_message",
                "payment_url",
                "status",
                "failed_at",
                "updated_at",
            ],
        )

        payment_attempt = locked_attempt

    return payment_attempt


def process_toman_deposit_callback(
        *,
        invoice_id: str,
        amount_rial,
        callback_status,
        reference_number: str = "",
        track_id: str = "",
) -> Transaction | None:
    invoice_id = str(
        invoice_id or "",
    ).strip()

    if not invoice_id:
        raise TomanDepositValidationError(
            message="شناسه فاکتور پرداخت ارسال نشده است.",
            code="PAYMENT_INVOICE_REQUIRED",
            status_code=400,
        )

    amount_rial = _parse_rial_amount(
        amount_rial,
    )

    with transaction.atomic():
        payment_attempt = (
            PaymentAttempt.objects
            .select_for_update()
            .select_related(
                "bank_account",
                "user",
            )
            .filter(
                invoice_id=invoice_id,
                gateway="nexpal",
            )
            .first()
        )

        if payment_attempt is None:
            payment_attempt = (
                PaymentAttempt.objects
                .select_for_update()
                .select_related(
                    "bank_account",
                    "user",
                )
                .filter(
                    gateway_reference=invoice_id,
                    gateway="nexpal",
                )
                .first()
            )

        if payment_attempt is None:
            raise TomanDepositValidationError(
                message="پرداخت پیدا نشد.",
                code="PAYMENT_NOT_FOUND",
                status_code=404,
            )

        if payment_attempt.status == "succeeded":
            try:
                return payment_attempt.transaction
            except Transaction.DoesNotExist:
                return None

        if (
                payment_attempt.expires_at
                and payment_attempt.expires_at <= timezone.now()
                and payment_attempt.status
                not in {
            "succeeded",
            "cancelled",
        }
        ):
            payment_attempt.status = "expired"
            payment_attempt.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )

            raise TomanDepositValidationError(
                message=(
                    "مهلت پرداخت به پایان رسیده است."
                ),
                code="PAYMENT_EXPIRED",
                status_code=410,
            )

        expected_amount_rial = int(
            payment_attempt.amount
            * Decimal("10")
        )

        if amount_rial != expected_amount_rial:
            payment_attempt.status = "failed"
            payment_attempt.failed_at = timezone.now()
            payment_attempt.gateway_code = (
                "AMOUNT_MISMATCH"
            )
            payment_attempt.gateway_message = (
                "Callback amount does not match PaymentAttempt amount."
            )

            payment_attempt.save(
                update_fields=[
                    "status",
                    "failed_at",
                    "gateway_code",
                    "gateway_message",
                    "updated_at",
                ],
            )

            raise TomanDepositValidationError(
                message=(
                    "مبلغ پرداخت با مبلغ درخواست "
                    "مطابقت ندارد."
                ),
                code="PAYMENT_AMOUNT_MISMATCH",
                status_code=409,
            )

        if not _is_successful_callback_status(
                callback_status,
        ):
            payment_attempt.status = "failed"
            payment_attempt.failed_at = timezone.now()
            payment_attempt.gateway_code = (
                "CALLBACK_FAILED"
            )
            payment_attempt.gateway_message = (
                "Gateway callback reported an unsuccessful payment."
            )

            payment_attempt.save(
                update_fields=[
                    "status",
                    "failed_at",
                    "gateway_code",
                    "gateway_message",
                    "updated_at",
                ],
            )

            return None

        if payment_attempt.callback_received_at is None:
            payment_attempt.callback_received_at = (
                timezone.now()
            )

        payment_attempt.status = (
            "verifying"
        )

        if reference_number:
            payment_attempt.gateway_reference = (
                str(reference_number)
            )

        if track_id:
            payment_attempt.gateway_message = (
                f"TrackId: {track_id}"
            )

        payment_attempt.save(
            update_fields=[
                "callback_received_at",
                "status",
                "gateway_reference",
                "gateway_message",
                "updated_at",
            ],
        )

    gateway = get_payment_gateway()

    gateway_token = _get_attempt_gateway_token(
        payment_attempt,
    )

    if not gateway_token:
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code="GATEWAY_TOKEN_MISSING",
            message=(
                "Payment gateway token is missing."
            ),
        )

        raise TomanDepositValidationError(
            message=(
                "اطلاعات پرداخت کامل نیست؛ "
                "لطفاً دوباره تلاش کنید."
            ),
            code="PAYMENT_GATEWAY_STATE_INVALID",
            status_code=503,
        )

    try:
        transaction_result = (
            gateway.get_transaction(
                token=gateway_token,
            )
        )
    except PaymentGatewayError as exc:
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code=(
                str(exc.code)
                if exc.code is not None
                else "TRANSACTION_QUERY_FAILED"
            ),
            message=exc.message,
        )

        raise TomanDepositValidationError(
            message=(
                "بررسی تراکنش پرداخت "
                "امکان‌پذیر نیست. دوباره تلاش کنید."
            ),
            code="PAYMENT_VERIFICATION_UNAVAILABLE",
            status_code=503,
        ) from exc

    if transaction_result.code == 12:
        with transaction.atomic():
            locked_attempt = (
                PaymentAttempt.objects
                .select_for_update()
                .get(
                    pk=payment_attempt.pk,
                )
            )

            if locked_attempt.status != "succeeded":
                locked_attempt.status = (
                    "callback_received"
                )
                locked_attempt.gateway_code = (
                    str(transaction_result.code)
                )
                locked_attempt.gateway_message = (
                    transaction_result.message
                )

                locked_attempt.save(
                    update_fields=[
                        "status",
                        "gateway_code",
                        "gateway_message",
                        "updated_at",
                    ],
                )

        return None

    if transaction_result.code != 100:
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code=str(
                transaction_result.code
            ),
            message=(
                    transaction_result.message
                    or "Gateway transaction is not verified."
            ),
        )

        raise TomanDepositValidationError(
            message=(
                "تراکنش پرداخت هنوز قابل تأیید نهایی نیست."
            ),
            code="PAYMENT_NOT_VERIFIED",
            status_code=409,
        )

    if (
            transaction_result.invoice_id
            and transaction_result.invoice_id
            != invoice_id
    ):
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code="TRANSACTION_INVOICE_MISMATCH",
            message=(
                "Gateway transaction invoice does not match "
                "the PaymentAttempt."
            ),
        )

        raise TomanDepositValidationError(
            message=(
                "شناسه پرداخت با تراکنش درگاه مطابقت ندارد."
            ),
            code="PAYMENT_INVOICE_MISMATCH",
            status_code=409,
        )

    if (
            transaction_result.amount_rial
            != expected_amount_rial
    ):
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code="TRANSACTION_AMOUNT_MISMATCH",
            message=(
                "Gateway transaction amount does not match "
                "the PaymentAttempt."
            ),
        )

        raise TomanDepositValidationError(
            message=(
                "مبلغ تراکنش درگاه با مبلغ پرداخت مطابقت ندارد."
            ),
            code="PAYMENT_AMOUNT_MISMATCH",
            status_code=409,
        )

    try:
        verify_result = (
            gateway.verify_payment(
                token=gateway_token,
            )
        )
    except PaymentGatewayError as exc:
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code=(
                str(exc.code)
                if exc.code is not None
                else "VERIFY_FAILED"
            ),
            message=exc.message,
        )

        raise TomanDepositValidationError(
            message=(
                "تأیید نهایی پرداخت انجام نشد."
            ),
            code="PAYMENT_VERIFY_FAILED",
            status_code=503,
        ) from exc

    if verify_result.code not in {
        100,
        13,
    }:
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code=str(
                verify_result.code
            ),
            message=(
                    verify_result.message
                    or "Gateway verification failed."
            ),
        )

        raise TomanDepositValidationError(
            message=(
                "تأیید نهایی پرداخت انجام نشد."
            ),
            code="PAYMENT_VERIFY_FAILED",
            status_code=409,
        )

    verify_amount = (
            verify_result.amount_rial
            or transaction_result.amount_rial
    )

    if verify_amount != expected_amount_rial:
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code="VERIFY_AMOUNT_MISMATCH",
            message=(
                "Gateway verify amount does not match "
                "the PaymentAttempt."
            ),
        )

        raise TomanDepositValidationError(
            message=(
                "مبلغ تأییدشده درگاه با مبلغ پرداخت مطابقت ندارد."
            ),
            code="PAYMENT_AMOUNT_MISMATCH",
            status_code=409,
        )

    if (
            verify_result.invoice_id
            and verify_result.invoice_id
            != invoice_id
    ):
        _mark_payment_attempt_failed(
            payment_attempt_id=payment_attempt.pk,
            code="VERIFY_INVOICE_MISMATCH",
            message=(
                "Gateway verify invoice does not match "
                "the PaymentAttempt."
            ),
        )

        raise TomanDepositValidationError(
            message=(
                "شناسه پرداخت تأییدشده با درخواست مطابقت ندارد."
            ),
            code="PAYMENT_INVOICE_MISMATCH",
            status_code=409,
        )

    with transaction.atomic():
        locked_attempt = (
            PaymentAttempt.objects
            .select_for_update()
            .get(
                pk=payment_attempt.pk,
            )
        )

        if locked_attempt.status == "succeeded":
            try:
                return locked_attempt.transaction
            except Transaction.DoesNotExist:
                return None

        locked_attempt.status = "verifying"
        locked_attempt.verified_at = (
                locked_attempt.verified_at
                or timezone.now()
        )

        locked_attempt.gateway_code = (
            str(verify_result.code)
        )

        locked_attempt.gateway_message = (
                verify_result.message
                or transaction_result.message
        )

        locked_attempt.save(
            update_fields=[
                "status",
                "verified_at",
                "gateway_code",
                "gateway_message",
                "updated_at",
            ],
        )

    return settle_toman_deposit(
        payment_attempt_id=payment_attempt.pk,
    )


@transaction.atomic
def settle_toman_deposit(
        *,
        payment_attempt_id,
) -> Transaction:
    payment_attempt = (
        PaymentAttempt.objects
        .select_for_update()
        .select_related(
            "bank_account",
            "user",
        )
        .get(
            pk=payment_attempt_id,
        )
    )

    if payment_attempt.status == "succeeded":
        if payment_attempt.transaction_id:
            return payment_attempt.transaction

        raise RuntimeError(
            "Succeeded PaymentAttempt has no transaction.",
        )

    if payment_attempt.verified_at is None:
        raise RuntimeError(
            "Cannot settle an unverified PaymentAttempt.",
        )

    user = (
        UserModel.objects
        .select_for_update()
        .get(
            pk=payment_attempt.user_id,
        )
    )

    daily_limit = (
        _get_daily_toman_deposit_limit()
    )

    used_today = (
        get_used_toman_deposit_today(
            user=user,
        )
    )

    remaining = (
            daily_limit - used_today
    )

    if remaining < payment_attempt.amount:
        raise TomanDepositValidationError(
            message=(
                "سقف واریز روزانه هنگام تسویه "
                "تکمیل شده است."
            ),
            code="DAILY_LIMIT_EXCEEDED",
            fields={
                "amount": (
                    "سقف باقی‌مانده واریز امروز کافی نیست."
                ),
            },
            status_code=409,
        )

    asset = _get_toman_asset()

    existing_transaction = (
        Transaction.objects
        .select_for_update()
        .filter(
            user_id=payment_attempt.user_id,
            idempotency_key=payment_attempt.idempotency_key,
            transaction_type="toman_deposit",
        )
        .first()
    )

    if existing_transaction is not None:
        payment_attempt.transaction = existing_transaction
        payment_attempt.status = "succeeded"

        if payment_attempt.verified_at is None:
            payment_attempt.verified_at = (
                    existing_transaction.completed_at
                    or timezone.now()
            )

        payment_attempt.save(
            update_fields=[
                "transaction",
                "status",
                "verified_at",
                "updated_at",
            ],
        )

        return existing_transaction

    now = timezone.now()

    deposit_transaction = (
        Transaction.objects.create(
            user=user,
            asset=asset,
            transaction_type="toman_deposit",
            amount=payment_attempt.amount,
            toman_amount=payment_attempt.amount,
            fee=Decimal("0"),
            bank_account_id=str(
                payment_attempt.bank_account_id
            ),
            idempotency_key=payment_attempt.idempotency_key,
            title="واریز تومان",
            description=(
                "تسویه واریز درگاه - "
                f"{_get_attempt_invoice_id(payment_attempt)}"
            ),
            status="completed",
            completed_at=now,
        )
    )

    credit_wallet(
        user_id=user.pk,
        asset_id=asset.pk,
        amount=payment_attempt.amount,
    )

    payment_attempt.transaction = deposit_transaction
    payment_attempt.status = "succeeded"

    if payment_attempt.verified_at is None:
        payment_attempt.verified_at = now

    payment_attempt.save(
        update_fields=[
            "transaction",
            "status",
            "verified_at",
            "updated_at",
        ],
    )

    return deposit_transaction


def create_toman_deposit_attempt(
        *,
        user,
        amount,
        bank_account_id: str,
        idempotency_key: str,
) -> PaymentAttempt:
    """
    Backward-compatible service name.

    New callers should use:
        start_toman_deposit_payment()
    """
    return start_toman_deposit_payment(
        user=user,
        amount=amount,
        bank_account_id=bank_account_id,
        idempotency_key=idempotency_key,
    )
