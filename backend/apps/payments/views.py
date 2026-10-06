from __future__ import annotations
from django.utils import timezone
from django.conf import settings
from django.shortcuts import get_object_or_404
from decimal import Decimal
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .gateways.base import PaymentGatewayError
from apps.transactions.serializers import TransactionSerializer

from .gateways import get_payment_gateway
from .models import PaymentAttempt
from .serializers import (
    TomanDepositCreateSerializer,
    TomanDepositResponseSerializer,
)
from .services import (
    TomanDepositValidationError,
    process_toman_deposit_callback,
    start_toman_deposit_payment,
)


def validation_error_response(
    exc: TomanDepositValidationError,
) -> Response:
    return Response(
        {
            "detail": exc.message,
            "code": exc.code,
            "details": {
                "fields": exc.fields or {},
            },
        },
        status=exc.status_code,
    )


class TomanDepositCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = TomanDepositCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        idempotency_key = request.headers.get(
            "Idempotency-Key",
            "",
        ).strip()

        try:
            payment_attempt = (
                start_toman_deposit_payment(
                    user=request.user,
                    amount=serializer.validated_data[
                        "amount"
                    ],
                    bank_account_id=(
                        serializer.validated_data[
                            "bankAccountId"
                        ]
                    ),
                    idempotency_key=idempotency_key,
                )
            )
        except TomanDepositValidationError as exc:
            return validation_error_response(
                exc,
            )

        response_serializer = (
            TomanDepositResponseSerializer(
                payment_attempt,
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class TomanDepositDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        pk,
        *args,
        **kwargs,
    ):
        payment_attempt = get_object_or_404(
            PaymentAttempt.objects.select_related(
                "bank_account",
                "user",
            ),
            id=pk,
            user=request.user,
        )

        serializer = (
            TomanDepositResponseSerializer(
                payment_attempt,
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class TomanDepositCallbackSerializer(
    serializers.Serializer,
):
    paymentRequestId = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )

    invoiceId = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=64,
    )

    amount = serializers.IntegerField(
        required=True,
        min_value=1,
    )

    status = serializers.BooleanField(
        required=True,
    )

    referenceNumber = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )

    trackId = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )


class NexpalTomanDepositCallbackAPIView(APIView):
    """
    Public gateway callback endpoint.

    The callback is NOT considered final payment proof.
    Final settlement still requires server-side transaction
    inquiry and verification against the provider.
    """

    permission_classes = [
        AllowAny,
    ]

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = (
            TomanDepositCallbackSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            transaction = (
                process_toman_deposit_callback(
                    invoice_id=(
                        serializer.validated_data[
                            "invoiceId"
                        ]
                    ),
                    amount_rial=(
                        serializer.validated_data[
                            "amount"
                        ]
                    ),
                    callback_status=(
                        serializer.validated_data[
                            "status"
                        ]
                    ),
                    reference_number=(
                        serializer.validated_data.get(
                            "referenceNumber",
                            "",
                        )
                    ),
                    track_id=(
                        serializer.validated_data.get(
                            "trackId",
                            "",
                        )
                    ),
                )
            )
        except TomanDepositValidationError as exc:
            return validation_error_response(
                exc,
            )

        payment_attempt = (
            PaymentAttempt.objects
            .select_related(
                "transaction",
            )
            .filter(
                invoice_id=(
                    serializer.validated_data[
                        "invoiceId"
                    ]
                ),
            )
            .first()
        )

        if transaction is not None:
            return Response(
                {
                    "status": "succeeded",
                    "transaction": (
                        TransactionSerializer(
                            transaction,
                        ).data
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": (
                    payment_attempt.status
                    if payment_attempt is not None
                    else "processing"
                ),
                "paymentAttemptId": (
                    str(payment_attempt.id)
                    if payment_attempt is not None
                    else None
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class TomanDepositTestPaymentAPIView(APIView):
    """
    Development-only payment page API.

    This endpoint simulates the external payment provider.
    It does NOT bypass verification or settlement.

    Flow:
        simulate provider payment
        -> callback processing
        -> transaction inquiry
        -> verify
        -> wallet settlement
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def _assert_development(self):
        if not settings.DEBUG:
            return Response(
                {
                    "detail": "Not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return None



    def get(
        self,
        request,
        token,
        *args,
        **kwargs,
    ):
        blocked = self._assert_development()

        if blocked is not None:
            return blocked

        payment_attempt = (
            PaymentAttempt.objects
            .select_related(
                "bank_account",
                "user",
            )
            .filter(
                user=request.user,
            )
            .filter(
                gateway_token=token,
            )
            .first()
        )

        if payment_attempt is None:
            payment_attempt = (
                PaymentAttempt.objects
                .select_related(
                    "bank_account",
                    "user",
                )
                .filter(
                    user=request.user,
                    gateway_authority=token,
                )
                .first()
            )

        if payment_attempt is None:
            return Response(
                {
                    "detail": "پرداخت پیدا نشد.",
                    "code": "PAYMENT_NOT_FOUND",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            TomanDepositResponseSerializer(
                payment_attempt,
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(
        self,
        request,
        token,
        *args,
        **kwargs,
    ):
        blocked = self._assert_development()

        if blocked is not None:
            return blocked

        gateway = get_payment_gateway()

        if gateway.name != "test_nexpal":
            return Response(
                {
                    "detail": (
                        "درگاه تست در محیط فعلی فعال نیست."
                    ),
                    "code": "TEST_GATEWAY_DISABLED",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        payment_attempt = (
            PaymentAttempt.objects
            .select_related(
                "bank_account",
                "user",
            )
            .filter(
                user=request.user,
                gateway_token=token,
            )
            .first()
        )

        if payment_attempt is None:
            payment_attempt = (
                PaymentAttempt.objects
                .select_related(
                    "bank_account",
                    "user",
                )
                .filter(
                    user=request.user,
                    gateway_authority=token,
                )
                .first()
            )

        if payment_attempt is None:
            return Response(
                {
                    "detail": "پرداخت پیدا نشد.",
                    "code": "PAYMENT_NOT_FOUND",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment_attempt.status == "succeeded":
            if payment_attempt.transaction_id:
                return Response(
                    TransactionSerializer(
                        payment_attempt.transaction,
                    ).data,
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "detail": (
                        "پرداخت موفق شده اما تراکنش "
                        "مالی آن پیدا نشد."
                    ),
                    "code": "SETTLEMENT_STATE_INVALID",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if (
            payment_attempt.expires_at
            and payment_attempt.expires_at
            <= timezone.now()
        ):
            if payment_attempt.status not in {
                "succeeded",
                "failed",
                "cancelled",
                "expired",
            }:
                payment_attempt.status = "expired"
                payment_attempt.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ],
                )

            return Response(
                {
                    "detail": (
                        "مهلت پرداخت به پایان رسیده است."
                    ),
                    "code": "PAYMENT_EXPIRED",
                },
                status=status.HTTP_410_GONE,
            )

        invoice_id = (
            str(
                payment_attempt.invoice_id
                or payment_attempt.gateway_reference
                or ""
            )
            .strip()
        )

        gateway_token = (
            str(
                payment_attempt.gateway_token
                or payment_attempt.gateway_authority
                or ""
            )
            .strip()
        )

        if not invoice_id or not gateway_token:
            return Response(
                {
                    "detail": (
                        "اطلاعات پرداخت کامل نیست."
                    ),
                    "code": "PAYMENT_STATE_INVALID",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if (
            payment_attempt.invoice_id
            != invoice_id
            or payment_attempt.gateway_token
            != gateway_token
        ):
            payment_attempt.invoice_id = invoice_id
            payment_attempt.gateway_token = gateway_token
            payment_attempt.save(
                update_fields=[
                    "invoice_id",
                    "gateway_token",
                    "updated_at",
                ],
            )

        amount_rial = int(
            payment_attempt.amount
            * Decimal("10")
        )

        try:
            gateway.register_existing_payment(
                token=gateway_token,
                invoice_id=invoice_id,
                amount_rial=amount_rial,
            )

            reference_number = (
                gateway.simulate_successful_payment(
                    token=gateway_token,
                )
            )
        except PaymentGatewayError as exc:
            return Response(
                {
                    "detail": (
                        "پرداخت آزمایشی انجام نشد."
                    ),
                    "code": "TEST_PAYMENT_FAILED",
                    "gatewayCode": (
                        str(exc.code)
                        if exc.code is not None
                        else None
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            transaction = (
                process_toman_deposit_callback(
                    invoice_id=invoice_id,
                    amount_rial=amount_rial,
                    callback_status=True,
                    reference_number=(
                        reference_number
                    ),
                )
            )
        except TomanDepositValidationError as exc:
            return validation_error_response(
                exc,
            )

        if transaction is None:
            payment_attempt = (
                PaymentAttempt.objects
                .get(
                    pk=payment_attempt.pk,
                )
            )

            return Response(
                {
                    "status": payment_attempt.status,
                    "paymentAttemptId": str(
                        payment_attempt.id,
                    ),
                },
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(
            TransactionSerializer(
                transaction,
            ).data,
            status=status.HTTP_200_OK,
        )