from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.transactions.serializers import TransactionSerializer

from .serializers_toman import (
    TomanWithdrawalCreateSerializer,
    TomanWithdrawalEstimateSerializer,
)
from .services.toman_withdrawal_service import (
    TomanWithdrawalValidationError,
    create_toman_withdrawal,
    create_toman_withdrawal_estimate,
)


def _withdrawal_error_response(exc):
    payload = {
        "detail": exc.message,
        "code": exc.code,
    }

    if exc.fields:
        payload["fields"] = exc.fields

    return Response(
        payload,
        status=exc.status_code,
    )


class TomanWithdrawalEstimateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TomanWithdrawalEstimateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            result = create_toman_withdrawal_estimate(
                user=request.user,
                amount=serializer.validated_data[
                    "amount"
                ],
                bank_account_id=serializer.validated_data[
                    "bankAccountId"
                ],
            )
        except TomanWithdrawalValidationError as exc:
            return _withdrawal_error_response(exc)

        return Response(
            {
                "estimateToken": result.estimate_token,
                "estimateVersion": result.estimate_version,
                "expiresAt": result.expires_at,
                "amount": result.amount,
                "bankAccountId": result.bank_account_id,
                "fee": result.fee,
                "receivable": result.receivable,
                "estimatedSettlement": (
                    result.estimated_settlement
                ),
            },
            status=status.HTTP_200_OK,
        )


class TomanWithdrawalCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TomanWithdrawalCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        idempotency_key = (
            request.headers.get(
                "Idempotency-Key",
                "",
            )
        )

        try:
            transaction = create_toman_withdrawal(
                user=request.user,
                estimate_token=serializer.validated_data[
                    "estimateToken"
                ],
                estimate_version=serializer.validated_data[
                    "estimateVersion"
                ],
                idempotency_key=idempotency_key,
            )
        except TomanWithdrawalValidationError as exc:
            return _withdrawal_error_response(exc)

        return Response(
            TransactionSerializer(
                transaction
            ).data,
            status=status.HTTP_200_OK,
        )