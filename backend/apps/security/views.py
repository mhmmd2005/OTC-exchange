from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LoginHistory, SecurityEvent
from .serializers import (
    AntiPhishingSerializer,
    LoginHistorySerializer,
    SecurityEventSerializer,
)
from .services import TwoFactorService


def build_security_overview(user):
    return {
        "mobileVerified": user.is_phone_verified,
        "emailVerified": user.email_verified_at is not None,
        "twoFactorEnabled": TwoFactorService.is_enabled(user),
        "antiPhishingEnabled": bool(user.anti_phishing_code),
        "antiPhishingCode": user.anti_phishing_code,
        "withdrawalWhitelistEnabled": False,
        "activeSessionsCount": 1,
    }


class SecurityOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            build_security_overview(request.user)
        )


class SecuritySessionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = None

        if request.auth:
            session_id = request.auth.get("session_id")

        return Response(
            [
                {
                    "id": str(session_id or "current"),
                    "device": "مرورگر فعلی",
                    "browser": "Browser",
                    "os": "Linux",
                    "ip_address": request.META.get("REMOTE_ADDR"),
                    "is_current": True,
                    "created_at": None,
                    "last_activity": None,
                }
            ]
        )


class SecuritySessionRevokeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):
        return Response(
            {
                "detail": (
                    "این قابلیت در این مرحله هنوز به "
                    "SessionService متصل نشده است."
                )
            },
            status=status.HTTP_200_OK,
        )


class SecurityOtherSessionsRevokeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        return Response(
            {
                "detail": (
                    "تمام نشست‌های دیگر در این مرحله نمایشی هستند."
                )
            },
            status=status.HTTP_200_OK,
        )


class SecurityEventListAPIView(generics.ListAPIView):
    serializer_class = SecurityEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SecurityEvent.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


class LoginHistoryListAPIView(generics.ListAPIView):
    serializer_class = LoginHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LoginHistory.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


class SecurityPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = (
                request.data.get(
                    "currentPassword"
                )
                or ""
        )

        new_password = (
                request.data.get(
                    "newPassword"
                )
                or ""
        )

        new_password_confirmation = (
                request.data.get(
                    "newPasswordConfirmation"
                )
                or ""
        )

        user = request.user

        if not user.check_password(
                current_password
        ):
            return Response(
                {
                    "detail": (
                        "رمز عبور فعلی صحیح نیست."
                    ),
                    "fields": {
                        "currentPassword": (
                            "رمز عبور فعلی صحیح نیست."
                        )
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {
                    "detail": (
                        "رمز جدید باید حداقل ۸ کاراکتر باشد."
                    ),
                    "fields": {
                        "newPassword": (
                            "رمز جدید باید حداقل ۸ کاراکتر باشد."
                        )
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
                new_password
                != new_password_confirmation
        ):
            return Response(
                {
                    "detail": (
                        "تکرار رمز عبور با رمز جدید یکسان نیست."
                    ),
                    "fields": {
                        "newPasswordConfirmation": (
                            "تکرار رمز عبور با رمز جدید یکسان نیست."
                        )
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
                current_password
                == new_password
        ):
            return Response(
                {
                    "detail": (
                        "رمز جدید باید با رمز فعلی متفاوت باشد."
                    ),
                    "fields": {
                        "newPassword": (
                            "رمز جدید باید با رمز فعلی متفاوت باشد."
                        )
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth.password_validation import (
            validate_password,
        )

        try:
            validate_password(
                new_password,
                user=user,
            )
        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": str(exc),
                    "fields": {
                        "newPassword": str(exc),
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(
            new_password
        )

        user.save(
            update_fields=[
                "password",
                "updated_at",
            ]
        )

        SecurityEvent.objects.create(
            user=user,
            event_type="password_change",
            description=(
                "رمز عبور حساب تغییر کرد."
            ),
            ip_address=request.META.get(
                "REMOTE_ADDR"
            ),
        )

        return Response(
            {
                "message": (
                    "رمز عبور با موفقیت تغییر کرد."
                )
            },
            status=status.HTTP_200_OK,
        )


class TwoFactorSetupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            setup = TwoFactorService.start_setup(
                request.user
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            setup,
            status=status.HTTP_200_OK,
        )


class TwoFactorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        enabled = bool(
            request.data.get(
                "enabled",
                False,
            )
        )

        request_ip = request.META.get(
            "REMOTE_ADDR"
        )

        if enabled:
            code = request.data.get("code")
            setup_token = request.data.get(
                "setupToken"
            )

            try:
                TwoFactorService.confirm_setup(
                    user=request.user,
                    code=code or "",
                    setup_token=setup_token or "",
                    request_ip=request_ip,
                )
            except DjangoValidationError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            code = request.data.get("code")

            try:
                TwoFactorService.disable(
                    user=request.user,
                    code=code or "",
                    request_ip=request_ip,
                )
            except DjangoValidationError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            build_security_overview(
                request.user
            ),
            status=status.HTTP_200_OK,
        )


class AntiPhishingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = AntiPhishingSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        old_code = (
                request.user.anti_phishing_code
                or ""
        ).strip()

        new_code = (
                serializer.validated_data.get(
                    "code"
                )
                or ""
        ).strip()

        if old_code == new_code:
            return Response(
                build_security_overview(
                    request.user
                ),
                status=status.HTTP_200_OK,
            )

        request.user.anti_phishing_code = new_code

        request.user.save(
            update_fields=[
                "anti_phishing_code",
                "updated_at",
            ]
        )

        if not old_code and new_code:
            event_type = "anti_phishing_created"
            description = (
                "کد ضد فیشینگ ثبت شد."
            )

        elif old_code and new_code:
            event_type = "anti_phishing_updated"
            description = (
                "کد ضد فیشینگ تغییر کرد."
            )

        else:
            event_type = "anti_phishing_deleted"
            description = (
                "کد ضد فیشینگ حذف شد."
            )

        SecurityEvent.objects.create(
            user=request.user,
            event_type=event_type,
            description=description,
            ip_address=request.META.get(
                "REMOTE_ADDR"
            ),
        )

        return Response(
            build_security_overview(
                request.user
            ),
            status=status.HTTP_200_OK,
        )


class WithdrawalWhitelistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        enabled = bool(
            request.data.get(
                "enabled",
                False,
            )
        )

        return Response(
            {
                "mobile_verified": (
                    request.user.is_phone_verified
                ),
                "email_verified": (
                        request.user.email_verified_at is not None
                ),
                "two_factor_enabled": (
                    TwoFactorService.is_enabled(
                        request.user
                    )
                ),
                "anti_phishing_code_enabled": False,
                "withdrawal_whitelist_enabled": enabled,
                "active_sessions_count": 1,
            }
        )
