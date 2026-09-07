from apps.accounts.serializers import (
    IdleTimeoutTokenRefreshSerializer,
    LoginPasswordSerializer,
    OTPVerifySerializer,
    PasswordResetSerializer,
    PhoneRequestSerializer,
    RegistrationPasswordSerializer,
    UserSerializer,
)
from apps.accounts.services.auth import AuthService
from apps.accounts.services.session import (
    delete_session,
    update_session,
)
from django.contrib.auth import get_user_model
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

User = get_user_model()


class RequestLoginOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PhoneRequestSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        phone_number = (
            serializer.validated_data[
                "phone_number"
            ]
        )

        result = AuthService.request_otp(
            phone_number,
            purpose="login",
            request_ip=request.META.get(
                "REMOTE_ADDR"
            ),
            user_agent=request.META.get(
                "HTTP_USER_AGENT",
                "",
            ),
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class RequestRegistrationOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PhoneRequestSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        phone_number = (
            serializer.validated_data[
                "phone_number"
            ]
        )

        result = AuthService.request_otp(
            phone_number,
            purpose="registration",
            request_ip=request.META.get(
                "REMOTE_ADDR"
            ),
            user_agent=request.META.get(
                "HTTP_USER_AGENT",
                "",
            ),
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = OTPVerifySerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            result = AuthService.verify_otp(
                challenge_id=str(
                    serializer.validated_data[
                        "challenge_id"
                    ]
                ),
                otp=serializer.validated_data[
                    "otp"
                ],
                request_ip=request.META.get(
                    "REMOTE_ADDR"
                ),
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class LoginVerifyPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginPasswordSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            result = AuthService.verify_login_password(
                flow_token=serializer.validated_data[
                    "flow_token"
                ],
                password=serializer.validated_data[
                    "password"
                ],
                request_ip=request.META.get(
                    "REMOTE_ADDR"
                ),
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class RegistrationSetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegistrationPasswordSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            result = AuthService.register_with_password(
                flow_token=serializer.validated_data[
                    "flow_token"
                ],
                password=serializer.validated_data[
                    "password"
                ],
                confirm_password=serializer.validated_data[
                    "confirm_password"
                ],
                request_ip=request.META.get(
                    "REMOTE_ADDR"
                ),
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get(
            "refresh"
        )

        if not refresh_token:
            return Response(
                {
                    "detail": (
                        "Refresh token is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(
                refresh_token
            )

            session_id = token.get(
                "session_id"
            )

            if session_id:
                delete_session(
                    session_id
                )

            token.blacklist()

        except Exception:
            return Response(
                {
                    "detail": (
                        "Invalid refresh token."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": (
                    "Logged out successfully."
                )
            },
            status=status.HTTP_200_OK,
        )


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        session_id = (
            request.auth.get("session_id")
            if request.auth
            else None
        )

        if not session_id:
            return Response(
                {
                    "detail": (
                        "Invalid authentication session."
                    )
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        is_activity = (
                request.headers.get(
                    "X-Activity-Heartbeat"
                )
                == "true"
        )

        if is_activity:
            if not update_session(
                    session_id,
                    request.user.id,
            ):
                return Response(
                    {
                        "detail": (
                            "Session expired."
                        )
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        serializer = UserSerializer(
            request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class AuthTokenRefreshView(TokenRefreshView):
    serializer_class = (
        IdleTimeoutTokenRefreshSerializer
    )
    permission_classes = [AllowAny]


class RequestPasswordResetOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PhoneRequestSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = AuthService.request_otp(
            serializer.validated_data[
                "phone_number"
            ],
            purpose="password_reset",
            request_ip=request.META.get(
                "REMOTE_ADDR"
            ),
            user_agent=request.META.get(
                "HTTP_USER_AGENT",
                "",
            ),
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            result = AuthService.reset_password(
                flow_token=serializer.validated_data[
                    "flow_token"
                ],
                password=serializer.validated_data[
                    "password"
                ],
                confirm_password=serializer.validated_data[
                    "confirm_password"
                ],
                request_ip=request.META.get(
                    "REMOTE_ADDR"
                ),
                user_agent=request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )
