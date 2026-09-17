from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import BankAccount
from .models import KycApplication
from .permissions import IsAdminUser
from .serializers import (
    BasicInfoSerializer,
    IdentityDocumentSerializer,
    KycApplicationSerializer,
    KycRejectSerializer,
    AdminKycApplicationSerializer
)


class GetOrCreateKycAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kyc, _ = KycApplication.objects.get_or_create(
            user=request.user,
        )
        return Response(
            KycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )


class KycStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kyc, _ = KycApplication.objects.get_or_create(
            user=request.user,
        )
        return Response(
            KycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )


class SubmitBasicInfoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        kyc, _ = KycApplication.objects.select_for_update().get_or_create(
            user=request.user,
        )

        if not request.user.is_phone_verified:
            return Response(
                {"detail": "ابتدا باید شماره موبایل خود را تأیید کنید."},
                status=status.HTTP_409_CONFLICT,
            )

        if not kyc.can_edit_basic_info:
            return Response(
                {"detail": "اطلاعات هویتی قابل ویرایش نیست."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = BasicInfoSerializer(
            kyc,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        kyc.basic_info_status = "pending"
        kyc.basic_info_submitted_at = timezone.now()
        kyc.basic_info_reviewed_at = None
        kyc.basic_info_reviewed_by = None
        kyc.basic_info_rejection_reason = ""

        kyc.save(update_fields=[
            "basic_info_status",
            "basic_info_submitted_at",
            "basic_info_reviewed_at",
            "basic_info_reviewed_by",
            "basic_info_rejection_reason",
            "updated_at",
        ])

        kyc.sync_status()

        return Response(
            {
                "id": str(kyc.id),
                "stepId": "basic_info",
                "status": "pending",
                "submittedAt": kyc.basic_info_submitted_at,
                "nextStep": "identity",
                "message": (
                    "اطلاعات هویتی با موفقیت ثبت شد. "
                    "حالا مدرک شناسایی خود را ارسال کنید."
                ),
            },
            status=status.HTTP_200_OK,
        )


class SubmitIdentityDocumentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request):
        kyc, _ = KycApplication.objects.select_for_update().get_or_create(
            user=request.user,
        )

        if not request.user.is_phone_verified:
            return Response(
                {"detail": "ابتدا باید شماره موبایل خود را تأیید کنید."},
                status=status.HTTP_409_CONFLICT,
            )

        if kyc.basic_info_status not in {"pending", "approved"}:
            return Response(
                {"detail": "ابتدا اطلاعات هویتی را ثبت کنید."},
                status=status.HTTP_409_CONFLICT,
            )

        if not kyc.can_edit_identity:
            return Response(
                {"detail": "مدرک شناسایی قابل ارسال یا ویرایش نیست."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = IdentityDocumentSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        kyc.identity_document = serializer.validated_data["document"]
        kyc.identity_status = "pending"
        kyc.identity_submitted_at = timezone.now()
        kyc.identity_reviewed_at = None
        kyc.identity_reviewed_by = None
        kyc.identity_rejection_reason = ""

        kyc.save(update_fields=[
            "identity_document",
            "identity_status",
            "identity_submitted_at",
            "identity_reviewed_at",
            "identity_reviewed_by",
            "identity_rejection_reason",
            "updated_at",
        ])

        kyc.sync_status()

        return Response(
            {
                "id": str(kyc.id),
                "stepId": "identity",
                "status": "pending",
                "submittedAt": kyc.identity_submitted_at,
                "nextStep": None,
                "reviewPending": True,
                "message": (
                    "اطلاعات شما برای بررسی ادمین ارسال شد. "
                    "نتیجه پس از بررسی در حساب شما اعلام می‌شود."
                ),
            },
            status=status.HTTP_200_OK,
        )


class AdminKycListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        queryset = KycApplication.objects.select_related(
            "user",
            "basic_info_reviewed_by",
            "identity_reviewed_by",
        )

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return Response(
            AdminKycApplicationSerializer(
                queryset,
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )


class AdminKycDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        try:
            kyc = KycApplication.objects.select_related(
                "user",
                "basic_info_reviewed_by",
                "identity_reviewed_by",
            ).get(pk=pk)
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            AdminKycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            kyc = KycApplication.objects.get(pk=pk)
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        kyc.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class AdminKycApproveStepAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, pk, step):
        try:
            kyc = KycApplication.objects.select_for_update().get(pk=pk)
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if step == "basic-info":
                kyc.approve_basic_info(request.user)
            elif step == "identity":
                kyc.approve_identity(request.user)
            else:
                return Response(
                    {"detail": "مرحله معتبر نیست."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            KycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )


class AdminKycRejectStepAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, pk, step):
        serializer = KycRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            kyc = KycApplication.objects.select_for_update().get(pk=pk)
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if step == "basic-info":
                kyc.reject_basic_info(
                    serializer.validated_data["reason"],
                    request.user,
                )
            elif step == "identity":
                kyc.reject_identity(
                    serializer.validated_data["reason"],
                    request.user,
                )
            else:
                return Response(
                    {"detail": "مرحله معتبر نیست."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            KycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )


class VerificationSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def map_status(value):
        return "verified" if value == "approved" else value

    def get(self, request):
        user = request.user
        kyc, _ = KycApplication.objects.get_or_create(
            user=user,
        )

        mobile_status = (
            "verified"
            if user.is_phone_verified
            else "not_started"
        )
        basic_status = self.map_status(
            kyc.basic_info_status,
        )
        identity_status = self.map_status(
            kyc.identity_status,
        )

        bank_unlocked = kyc.both_identity_steps_approved
        bank_status = "not_started"

        if bank_unlocked:
            if BankAccount.objects.filter(
                    user=user,
                    status="verified",
            ).exists():
                bank_status = "verified"
            elif BankAccount.objects.filter(
                    user=user,
                    status="pending",
            ).exists():
                bank_status = "pending"
            elif BankAccount.objects.filter(
                    user=user,
                    status="rejected",
            ).exists():
                bank_status = "rejected"

        review_pending = (
                not (
                        kyc.basic_info_status == "rejected"
                        or kyc.identity_status == "rejected"
                        or bank_status == "rejected"
                )
                and (
                        kyc.basic_info_status == "pending"
                        or kyc.identity_status == "pending"
                        or bank_status == "pending"
                )
        )

        if not user.is_phone_verified:
            current_step_id = "mobile"
        elif kyc.basic_info_status == "rejected":
            current_step_id = "basic_info"
        elif kyc.identity_status == "rejected":
            current_step_id = "identity"
        elif kyc.basic_info_status == "not_started":
            current_step_id = "basic_info"
        elif kyc.identity_status == "not_started":
            current_step_id = "identity"
        elif bank_unlocked and bank_status in {"not_started", "rejected"}:
            current_step_id = "bank"
        else:
            current_step_id = None

        steps = [
            {
                "id": "mobile",
                "title": "تأیید شماره موبایل",
                "description": "مالکیت شماره موبایل خود را تأیید کنید.",
                "status": mobile_status,
                "required": True,
                "locked": mobile_status == "verified",
                "actionLabel": (
                    "دریافت کد تأیید"
                    if mobile_status != "verified"
                    else None
                ),
            },
            {
                "id": "basic_info",
                "title": "اطلاعات هویتی",
                "description": "نام، نام خانوادگی، کد ملی و تاریخ تولد را وارد کنید.",
                "status": basic_status,
                "required": True,
                "locked": not kyc.can_edit_basic_info,
                "actionLabel": (
                    "ارسال مجدد"
                    if kyc.basic_info_status == "rejected"
                    else "ثبت اطلاعات"
                    if kyc.basic_info_status == "not_started"
                    else None
                ),
                "rejectionReason": (
                    kyc.basic_info_rejection_reason
                    if kyc.basic_info_status == "rejected"
                    else None
                ),
                "completedAt": (
                    kyc.basic_info_reviewed_at
                    if kyc.basic_info_status == "approved"
                    else None
                ),
            },
            {
                "id": "identity",
                "title": "مدرک شناسایی",
                "description": "مدرک شناسایی خود را برای بررسی ارسال کنید.",
                "status": identity_status,
                "required": True,
                "locked": not kyc.can_edit_identity,
                "actionLabel": (
                    "ارسال مجدد"
                    if kyc.identity_status == "rejected"
                    else "ارسال مدرک"
                    if kyc.identity_status == "not_started"
                    else None
                ),
                "rejectionReason": (
                    kyc.identity_rejection_reason
                    if kyc.identity_status == "rejected"
                    else None
                ),
                "completedAt": (
                    kyc.identity_reviewed_at
                    if kyc.identity_status == "approved"
                    else None
                ),
            },
            {
                "id": "bank",
                "title": "حساب بانکی",
                "description": "یک حساب بانکی به نام خودتان اضافه کنید.",
                "status": bank_status,
                "required": True,
                "locked": not bank_unlocked,
                "actionLabel": (
                    "افزودن حساب بانکی"
                    if bank_unlocked
                       and bank_status in {"not_started", "rejected"}
                    else None
                ),
                "actionRoute": "/app/bank-accounts",
            },
        ]

        if bank_status == "verified":
            verification_status = "verified"
        elif (
                kyc.basic_info_status == "rejected"
                or kyc.identity_status == "rejected"
                or bank_status == "rejected"
        ):
            verification_status = "rejected"
        elif review_pending:
            verification_status = "pending"
        elif any(
                step["status"] != "not_started"
                for step in steps
        ):
            verification_status = "in_progress"
        else:
            verification_status = "not_started"

        verified_count = sum(
            step["status"] == "verified"
            for step in steps
        )
        progress = round(
            verified_count / len(steps) * 100,
        )

        if verification_status == "verified":
            message = "احراز هویت شما با موفقیت تکمیل شده است."
        elif review_pending:
            message = (
                "اطلاعات هویتی و مدرک شناسایی شما "
                "برای بررسی ادمین ارسال شده است. "
                "نتیجه پس از بررسی در حساب شما اعلام می‌شود."
            )
        elif verification_status == "rejected":
            message = "یکی از مراحل احراز هویت نیاز به اصلاح دارد."
        else:
            message = (
                "برای تکمیل احراز هویت، مراحل باقی‌مانده را انجام دهید."
            )

        current_level = user.kyc_level or "level_0"

        return Response({
            "status": verification_status,
            "currentLevel": current_level,
            "progressPercent": progress,
            "message": message,
            "currentStepId": current_step_id,
            "reviewPending": review_pending,
            "basicInfo": {
                "firstName": kyc.first_name,
                "lastName": kyc.last_name,
                "nationalId": kyc.national_id,
                "birthDate": (
                    kyc.birth_date.isoformat()
                    if kyc.birth_date
                    else ""
                ),
            },
            "steps": steps,
            "levels": [],
            "limits": {
                "accountLevel": current_level,
                "dailyBuy": "0",
                "dailySell": "0",
                "dailyTomanDeposit": "0",
                "dailyTomanWithdrawal": "0",
                "dailyCryptoWithdrawalTomanEquivalent": "0",
                "usedBuy": "0",
                "usedSell": "0",
                "usedTomanDeposit": "0",
                "usedTomanWithdrawal": "0",
                "usedCryptoWithdrawalTomanEquivalent": "0",
            },
        })


class AdminKycApproveBankAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, pk, bank_id):
        try:
            kyc = KycApplication.objects.select_for_update().get(
                pk=pk,
            )
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not kyc.both_identity_steps_approved:
            return Response(
                {
                    "detail": (
                        "ابتدا باید هر دو مرحله احراز هویت تأیید شوند."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            account = BankAccount.objects.select_for_update().get(
                pk=bank_id,
                user=kyc.user,
            )
        except BankAccount.DoesNotExist:
            return Response(
                {"detail": "Bank account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            account.approve()
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AdminKycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )


class AdminKycRejectBankAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, pk, bank_id):
        serializer = KycRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            kyc = KycApplication.objects.select_for_update().get(
                pk=pk,
            )
        except KycApplication.DoesNotExist:
            return Response(
                {"detail": "KYC application not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            account = BankAccount.objects.select_for_update().get(
                pk=bank_id,
                user=kyc.user,
            )
        except BankAccount.DoesNotExist:
            return Response(
                {"detail": "Bank account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            account.reject(
                serializer.validated_data["reason"],
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AdminKycApplicationSerializer(kyc).data,
            status=status.HTTP_200_OK,
        )
