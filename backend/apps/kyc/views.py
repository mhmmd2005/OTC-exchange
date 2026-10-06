import jdatetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import BankAccount
from apps.payments.services import get_toman_deposit_limit_data
from .models import KycApplication
from .serializers import (
    BasicInfoSerializer,
    IdentityDocumentSerializer,
    KycApplicationSerializer,
)
from .services.ehraz import EhrazAPIError, EhrazService


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

        if not settings.EHRAZ_API_TOKEN:
            return Response(
                {
                    "detail": (
                        "سرویس احراز هویت هنوز پیکربندی نشده است."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        data = serializer.validated_data

        full_name = (
            f"{data['first_name']} {data['last_name']}"
        ).strip()

        birth_date = jdatetime.date.fromgregorian(
            date=data["birth_date"]
        ).strftime("%Y%m%d")

        try:
            mobile_result = (
                EhrazService.match_national_with_mobile(
                    national_code=data["national_id"],
                    mobile_number=request.user.phone_number,
                )
            )

            if "matched" not in mobile_result:
                raise EhrazAPIError(
                    "پاسخ تطبیق کد ملی و موبایل ناقص است."
                )

            if mobile_result["matched"] is not True:
                serializer.save()

                now = timezone.now()

                kyc.basic_info_status = "rejected"
                kyc.basic_info_submitted_at = now
                kyc.basic_info_reviewed_at = now
                kyc.basic_info_reviewed_by = None
                kyc.basic_info_rejection_reason = (
                    "کد ملی با شماره موبایل ثبت‌شده مطابقت ندارد."
                )
                kyc.rejection_reason = (
                    kyc.basic_info_rejection_reason
                )

                kyc.save(
                    update_fields=[
                        "basic_info_status",
                        "basic_info_submitted_at",
                        "basic_info_reviewed_at",
                        "basic_info_reviewed_by",
                        "basic_info_rejection_reason",
                        "rejection_reason",
                        "updated_at",
                    ]
                )

                kyc.sync_status()

                return Response(
                    {
                        "id": str(kyc.id),
                        "stepId": "basic_info",
                        "status": "rejected",
                        "submittedAt": kyc.basic_info_submitted_at,
                        "nextStep": "basic_info",
                        "reviewPending": False,
                        "rejectionReason": (
                            kyc.basic_info_rejection_reason
                        ),
                        "message": (
                            "کد ملی و شماره موبایل شما توسط "
                            "سرویس احراز با یکدیگر مطابقت ندارند."
                        ),
                    },
                    status=status.HTTP_200_OK,
                )

            identity_result = (
                EhrazService.identity_similarity(
                    national_code=data["national_id"],
                    birth_date=birth_date,
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    full_name=full_name,
                    father_name=data["father_name"],
                )
            )

            identity_matched = (
                EhrazService.identity_similarity_matches(
                    identity_result,
                    threshold=(
                        settings.EHRAZ_IDENTITY_SIMILARITY_THRESHOLD
                    ),
                )
            )

            serializer.save()

            now = timezone.now()

            if not identity_matched:
                kyc.basic_info_status = "rejected"
                kyc.basic_info_submitted_at = now
                kyc.basic_info_reviewed_at = now
                kyc.basic_info_reviewed_by = None
                kyc.basic_info_rejection_reason = (
                    "اطلاعات هویتی واردشده با اطلاعات ثبت‌شده مطابقت ندارد. "
                    "لطفاً نام، نام خانوادگی، نام پدر، کد ملی و تاریخ تولد را "
                    "دقیقاً مطابق مدارک رسمی وارد کنید."
                )
                kyc.rejection_reason = (
                    kyc.basic_info_rejection_reason
                )

                kyc.save(
                    update_fields=[
                        "basic_info_status",
                        "basic_info_submitted_at",
                        "basic_info_reviewed_at",
                        "basic_info_reviewed_by",
                        "basic_info_rejection_reason",
                        "rejection_reason",
                        "updated_at",
                    ]
                )

                kyc.sync_status()

                return Response(
                    {
                        "id": str(kyc.id),
                        "stepId": "basic_info",
                        "status": "rejected",
                        "submittedAt": kyc.basic_info_submitted_at,
                        "nextStep": "basic_info",
                        "reviewPending": False,
                        "rejectionReason": (
                            kyc.basic_info_rejection_reason
                        ),
                        "message": (
                            "اطلاعات هویتی واردشده با اطلاعات ثبت‌شده مطابقت ندارد. "
                            "لطفاً در ارسال اطلاعات دقت فرمایید."
                        ),
                    },
                    status=status.HTTP_200_OK,
                )

            kyc.basic_info_status = "approved"
            kyc.basic_info_submitted_at = now
            kyc.basic_info_reviewed_at = now
            kyc.basic_info_reviewed_by = None
            kyc.basic_info_rejection_reason = ""
            kyc.rejection_reason = ""

            kyc.save(
                update_fields=[
                    "basic_info_status",
                    "basic_info_submitted_at",
                    "basic_info_reviewed_at",
                    "basic_info_reviewed_by",
                    "basic_info_rejection_reason",
                    "rejection_reason",
                    "updated_at",
                ]
            )

            kyc.sync_status()

        except EhrazAPIError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "id": str(kyc.id),
                "stepId": "basic_info",
                "status": "approved",
                "submittedAt": kyc.basic_info_submitted_at,
                "nextStep": "identity",
                "reviewPending": False,
                "message": (
                    "اطلاعات هویتی شما تأیید شد. "
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

        if kyc.basic_info_status != "approved":
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

        kyc.identity_document_front = serializer.validated_data["front"]
        kyc.identity_document_back = serializer.validated_data["back"]

        kyc.identity_status = "pending"
        kyc.identity_submitted_at = timezone.now()
        kyc.identity_reviewed_at = None
        kyc.identity_reviewed_by = None
        kyc.identity_rejection_reason = ""

        kyc.save(update_fields=[
            "identity_document_front",
            "identity_document_back",
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

        elif bank_unlocked and bank_status in {
            "not_started",
            "rejected",
        }:
            current_step_id = "bank"

        else:
            current_step_id = None

        steps = [
            {
                "id": "mobile",
                "title": "تأیید شماره موبایل",
                "description": (
                    "مالکیت شماره موبایل خود را تأیید کنید."
                ),
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
                "description": (
                    "نام، نام خانوادگی، نام پدر، "
                    "کد ملی و تاریخ تولد را وارد کنید."
                ),
                "status": basic_status,
                "required": True,
                "locked": not kyc.can_edit_basic_info,
                "actionLabel": (
                    "ارسال مجدد"
                    if kyc.basic_info_status == "rejected"
                    else (
                        "ثبت اطلاعات"
                        if kyc.basic_info_status == "not_started"
                        else None
                    )
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
                "description": (
                    "مدرک شناسایی خود را برای بررسی ارسال کنید."
                ),
                "status": identity_status,
                "required": True,
                "locked": not kyc.can_edit_identity,
                "actionLabel": (
                    "ارسال مجدد"
                    if kyc.identity_status == "rejected"
                    else (
                        "ارسال مدرک"
                        if kyc.identity_status == "not_started"
                        else None
                    )
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
                "description": (
                    "یک حساب بانکی به نام خودتان اضافه کنید."
                ),
                "status": bank_status,
                "required": True,
                "locked": not bank_unlocked,
                "actionLabel": (
                    "افزودن حساب بانکی"
                    if (
                            bank_unlocked
                            and bank_status in {
                                "not_started",
                                "rejected",
                            }
                    )
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
            message = (
                "احراز هویت شما با موفقیت تکمیل شده است."
            )

        elif (
                review_pending
                and kyc.identity_status == "pending"
        ):
            message = (
                "مدرک شناسایی شما برای بررسی ادمین ارسال شده است. "
                "نتیجه پس از بررسی در حساب شما اعلام می‌شود."
            )

        elif (
                review_pending
                and bank_status == "pending"
        ):
            message = (
                "حساب بانکی شما برای بررسی ادمین ارسال شده است. "
                "نتیجه پس از بررسی در حساب شما اعلام می‌شود."
            )

        elif verification_status == "rejected":
            message = (
                "یکی از مراحل احراز هویت نیاز به اصلاح دارد."
            )

        else:
            message = (
                "برای تکمیل احراز هویت، مراحل باقی‌مانده را انجام دهید."
            )

        current_level = user.kyc_level or "level_0"

        toman_deposit_limits = get_toman_deposit_limit_data(
            user=user,
        )

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
                "fatherName": kyc.father_name,
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

                "dailyTomanDeposit": str(
                    toman_deposit_limits["daily"]
                ),

                "dailyTomanWithdrawal": "0",
                "dailyCryptoWithdrawalTomanEquivalent": "0",

                "usedBuy": "0",
                "usedSell": "0",

                "usedTomanDeposit": str(
                    toman_deposit_limits["used"]
                ),

                "usedTomanWithdrawal": "0",
                "usedCryptoWithdrawalTomanEquivalent": "0",
            },
        })
