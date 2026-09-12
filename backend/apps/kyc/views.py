from django.db import transaction
from rest_framework import status
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import KycApplication
from .permissions import IsAdminUser
from .serializers import KycApplicationSerializer


class GetOrCreateKycAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kyc, _ = KycApplication.objects.get_or_create(user=request.user)
        serializer = KycApplicationSerializer(kyc)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitKycAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request):
        kyc, _ = KycApplication.objects.get_or_create(user=request.user)

        if not kyc.can_submit:
            return Response(
                {"detail": f"Cannot submit KYC with status '{kyc.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = KycApplicationSerializer(
            kyc,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        kyc.submit()

        return Response(
            KycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )


class UpdateKycAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def patch(self, request):
        kyc, _ = KycApplication.objects.get_or_create(user=request.user)

        if not kyc.can_edit:
            return Response(
                {"detail": f"Cannot edit KYC with status '{kyc.get_status_display()}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = KycApplicationSerializer(
            kyc,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class KycStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kyc, _ = KycApplication.objects.get_or_create(user=request.user)
        serializer = KycApplicationSerializer(kyc)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminKycListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get("status")
        queryset = KycApplication.objects.all()

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = KycApplicationSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminKycDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        try:
            kyc = KycApplication.objects.get(pk=pk)
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = KycApplicationSerializer(kyc)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminKycApproveAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, pk):
        try:
            kyc = KycApplication.objects.get(pk=pk)
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if kyc.status != "pending":
            return Response(
                {"detail": "این درخواست در وضعیت قابل تأیید نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        kyc.approve(reviewed_by=request.user)

        return Response(
            KycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )


class AdminKycRejectAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request, pk):
        try:
            kyc = KycApplication.objects.get(pk=pk)
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if kyc.status != "pending":
            return Response(
                {"detail": "این درخواست در وضعیت قابل رد نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = str(request.data.get("reason", "")).strip()

        if not reason:
            return Response(
                {"detail": "دلیل رد درخواست را وارد کنید."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        kyc.reject(reason, reviewed_by=request.user)

        return Response(
            KycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )


class VerificationSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "status": "not_started",
            "currentLevel": "level_0",
            "progressPercent": 0,
            "message": "برای تکمیل احراز هویت، مراحل باقی‌مانده را انجام دهید.",
            "steps": [
                {
                    "id": "mobile",
                    "title": "تأیید شماره موبایل",
                    "description": "مالکیت شماره موبایل خود را تأیید کنید.",
                    "status": "not_started",
                    "required": True,
                    "actionLabel": "دریافت کد تأیید"
                },
                {
                    "id": "basic_info",
                    "title": "اطلاعات هویتی",
                    "description": "نام، نام خانوادگی، کد ملی و تاریخ تولد را وارد کنید.",
                    "status": "not_started",
                    "required": True,
                    "actionLabel": "ثبت اطلاعات"
                },
                {
                    "id": "identity",
                    "title": "مدرک شناسایی",
                    "description": "مدرک شناسایی خود را برای بررسی ارسال کنید.",
                    "status": "not_started",
                    "required": True,
                    "actionLabel": "ارسال مدرک"
                },
                {
                    "id": "bank",
                    "title": "حساب بانکی",
                    "description": "یک حساب بانکی به نام خودتان اضافه کنید.",
                    "status": "not_started",
                    "required": True,
                    "actionLabel": "افزودن حساب بانکی",
                    "actionRoute": "/app/bank-accounts"
                },
                {
                    "id": "selfie",
                    "title": "تصویر چهره",
                    "description": "تصویر چهره خود را برای بررسی ارسال کنید.",
                    "status": "not_started",
                    "required": False,
                    "actionLabel": "ارسال تصویر"
                }
            ],
            "levels": [],
            "limits": {
                "accountLevel": "level_0",
                "dailyBuy": "0",
                "dailySell": "0",
                "dailyTomanDeposit": "0",
                "dailyTomanWithdrawal": "0",
                "dailyCryptoWithdrawalTomanEquivalent": "0",
                "usedBuy": "0",
                "usedSell": "0",
                "usedTomanDeposit": "0",
                "usedTomanWithdrawal": "0",
                "usedCryptoWithdrawalTomanEquivalent": "0"
            }
        })
