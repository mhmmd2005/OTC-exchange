from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LoginHistory, SecurityEvent
from .serializers import LoginHistorySerializer, SecurityEventSerializer


class SecurityOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "two_factor_enabled": False,
            "anti_phishing_code_enabled": False,
            "withdrawal_whitelist_enabled": False,
            "active_sessions_count": 1,
        })


class SecuritySessionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = None

        if request.auth:
            session_id = request.auth.get("session_id")

        return Response([
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
        ])


class SecuritySessionRevokeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):
        return Response(
            {"detail": "این قابلیت در این مرحله هنوز به SessionService متصل نشده است."},
            status=status.HTTP_200_OK,
        )


class SecurityOtherSessionsRevokeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        return Response(
            {"detail": "تمام نشست‌های دیگر در این مرحله نمایشی هستند."},
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
        return Response(
            {
                "message": "تغییر رمز عبور در مرحله بعد به منطق امنیتی متصل می‌شود."
            },
            status=status.HTTP_200_OK,
        )


class TwoFactorSetupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({
            "setup_token": "",
            "secret": "",
            "qr_code": "",
            "enabled": False,
        })


class TwoFactorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        enabled = bool(request.data.get("enabled", False))

        return Response({
            "two_factor_enabled": enabled,
            "anti_phishing_code_enabled": False,
            "withdrawal_whitelist_enabled": False,
            "active_sessions_count": 1,
        })


class AntiPhishingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        code = request.data.get("code")

        return Response({
            "two_factor_enabled": False,
            "anti_phishing_code_enabled": bool(code),
            "withdrawal_whitelist_enabled": False,
            "active_sessions_count": 1,
        })


class WithdrawalWhitelistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        enabled = bool(
            request.data.get(
                "enabled",
                False,
            )
        )

        return Response({
            "two_factor_enabled": False,
            "anti_phishing_code_enabled": False,
            "withdrawal_whitelist_enabled": enabled,
            "active_sessions_count": 1,
        })
