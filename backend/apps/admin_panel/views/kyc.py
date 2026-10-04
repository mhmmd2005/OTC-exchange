from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import BankAccount
from apps.kyc.models import KycApplication
from ..authentication import AdminJWTAuthentication
from ..permissions import IsAdminAuthenticated
from ..serializers import (
    AdminKycApplicationSerializer,
    KycRejectSerializer,
)


class AdminKycListAPIView(APIView):
    authentication_classes = [
        AdminJWTAuthentication,
    ]
    permission_classes = [
        IsAdminAuthenticated,
    ]

    def get(self, request):
        queryset = (
            KycApplication.objects
            .select_related(
                "user",
                "basic_info_reviewed_by",
                "identity_reviewed_by",
                "reviewed_by",
            )
        )

        status_filter = request.query_params.get(
            "status",
        )

        if status_filter:
            queryset = queryset.filter(
                status=status_filter,
            )

        return Response(
            AdminKycApplicationSerializer(
                queryset,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )


class AdminKycDetailAPIView(APIView):
    authentication_classes = [
        AdminJWTAuthentication,
    ]
    permission_classes = [
        IsAdminAuthenticated,
    ]

    def get(self, request, pk):
        try:
            kyc = (
                KycApplication.objects
                .select_related(
                    "user",
                    "basic_info_reviewed_by",
                    "identity_reviewed_by",
                    "reviewed_by",
                )
                .get(pk=pk)
            )
        except KycApplication.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "درخواست احراز هویت پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            AdminKycApplicationSerializer(
                kyc,
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            kyc = KycApplication.objects.get(
                pk=pk,
            )
        except KycApplication.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "درخواست احراز هویت پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        kyc.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class AdminKycApproveStepAPIView(APIView):
    authentication_classes = [
        AdminJWTAuthentication,
    ]
    permission_classes = [
        IsAdminAuthenticated,
    ]

    @transaction.atomic
    def post(self, request, pk, step):
        try:
            kyc = (
                KycApplication.objects
                .select_for_update()
                .get(pk=pk)
            )
        except KycApplication.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "درخواست احراز هویت پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if step == "basic-info":
                return Response(
                    {
                        "detail": (
                            "اطلاعات هویتی توسط سرویس احراز بررسی "
                            "می‌شود و قابل تأیید دستی نیست."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            if step == "identity":
                kyc.approve_identity(
                    request.user,
                )
            else:
                return Response(
                    {
                        "detail": "مرحله معتبر نیست."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AdminKycApplicationSerializer(
                kyc,
            ).data,
            status=status.HTTP_200_OK,
        )


class AdminKycRejectStepAPIView(APIView):
    authentication_classes = [
        AdminJWTAuthentication,
    ]
    permission_classes = [
        IsAdminAuthenticated,
    ]

    @transaction.atomic
    def post(self, request, pk, step):
        if step == "basic-info":
            return Response(
                {
                    "detail": (
                        "اطلاعات هویتی توسط سرویس احراز بررسی می‌شود "
                        "و قابل رد دستی نیست."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        if step != "identity":
            return Response(
                {
                    "detail": "مرحله معتبر نیست."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = KycRejectSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            kyc = (
                KycApplication.objects
                .select_for_update()
                .get(pk=pk)
            )
        except KycApplication.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "درخواست احراز هویت پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            kyc.reject_identity(
                serializer.validated_data["reason"],
                request.user,
            )
        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AdminKycApplicationSerializer(
                kyc,
            ).data,
            status=status.HTTP_200_OK,
        )


class AdminKycApproveBankAPIView(APIView):
    authentication_classes = [
        AdminJWTAuthentication,
    ]
    permission_classes = [
        IsAdminAuthenticated,
    ]

    @transaction.atomic
    def post(self, request, pk, bank_id):
        try:
            kyc = (
                KycApplication.objects
                .select_for_update()
                .get(pk=pk)
            )
        except KycApplication.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "درخواست احراز هویت پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not kyc.both_identity_steps_approved:
            return Response(
                {
                    "detail": (
                        "ابتدا باید هر دو مرحله "
                        "احراز هویت تأیید شوند."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            account = (
                BankAccount.objects
                .select_for_update()
                .get(
                    pk=bank_id,
                    user=kyc.user,
                )
            )
        except BankAccount.DoesNotExist:
            return Response(
                {
                    "detail": "حساب بانکی پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            account.approve()
            kyc.sync_status()

        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AdminKycApplicationSerializer(
                kyc,
            ).data,
            status=status.HTTP_200_OK,
        )


class AdminKycRejectBankAPIView(APIView):
    authentication_classes = [
        AdminJWTAuthentication,
    ]
    permission_classes = [
        IsAdminAuthenticated,
    ]

    @transaction.atomic
    def post(self, request, pk, bank_id):
        serializer = KycRejectSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            kyc = (
                KycApplication.objects
                .select_for_update()
                .get(pk=pk)
            )
        except KycApplication.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "درخواست احراز هویت پیدا نشد."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            account = (
                BankAccount.objects
                .select_for_update()
                .get(
                    pk=bank_id,
                    user=kyc.user,
                )
            )
        except BankAccount.DoesNotExist:
            return Response(
                {
                    "detail": "حساب بانکی پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            account.reject(
                serializer.validated_data["reason"],
            )
            kyc.sync_status()

        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AdminKycApplicationSerializer(
                kyc,
            ).data,
            status=status.HTTP_200_OK,
        )
