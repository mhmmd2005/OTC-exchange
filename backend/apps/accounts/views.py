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

from apps.accounts.models import BankAccount, IranianBank
from apps.accounts.serializers import (
    BankAccountSerializer,
    DashboardSummarySerializer,
    IdleTimeoutTokenRefreshSerializer,
    IranianBankSerializer,
    LoginPasswordSerializer,
    OTPVerifySerializer,
    PasswordResetSerializer,
    PhoneRequestSerializer,
    RegistrationPasswordSerializer,
    UserPreferencesSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from apps.accounts.services.auth import AuthService
from apps.accounts.services.session import (
    delete_session,
    update_session,
)

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


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserPreferencesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Return default preferences for now
        # In production, this would be stored in a UserPreferences model
        serializer = UserPreferencesSerializer({
            "language": "fa",
            "theme": "system",
            "notificationChannels": {
                "email": True,
                "sms": True,
                "push": True
            },
            "priceAlerts": True,
            "securityAlerts": True,
            "marketingEmails": False
        })
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = UserPreferencesSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        # In production, save to UserPreferences model
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class DashboardSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Return safe default values for now
        # In production, this would aggregate real wallet, order, and notification data
        from apps.wallets.models import Wallet
        from apps.orders.models import Order
        from apps.notifications.models import Notification

        user = request.user

        # Get wallet data (safe defaults if no wallet exists)
        try:
            toman_wallet = Wallet.objects.filter(
                user=user,
                asset__symbol="IRT"
            ).first()
            toman_balance = str(toman_wallet.available_balance) if toman_wallet else "0"
        except:
            toman_balance = "0"

        # Get pending orders count
        pending_orders_count = Order.objects.filter(
            user=user,
            status__in=["pending", "open", "partially_filled"]
        ).count()

        # Get unread notifications count
        unread_notifications_count = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()

        serializer = DashboardSummarySerializer({
            "user": user,
            "totalPortfolioToman": toman_balance,
            "tomanBalance": toman_balance,
            "cryptoValueToman": "0",
            "pendingOrdersCount": pending_orders_count,
            "unreadNotificationsCount": unread_notifications_count,
        })
        return Response(serializer.data, status=status.HTTP_200_OK)


class IranianBankListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        banks = IranianBank.objects.all()
        serializer = IranianBankSerializer(banks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BankAccountListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = BankAccount.objects.filter(
            user=request.user
        )

        serializer = BankAccountSerializer(
            accounts,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        card_number = str(
            request.data.get("cardNumber", "")
        )

        iban = str(
            request.data.get("iban", "")
        )

        account_number = str(
            request.data.get("accountNumber", "")
        )

        owner_name = request.user.full_name or ""

        card_digits = "".join(
            char for char in card_number
            if char.isdigit()
        )

        if len(card_digits) != 16:
            return Response(
                {
                    "fields": {
                        "cardNumber": "شماره کارت باید ۱۶ رقم باشد."
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            bank = None
            card_bin = card_digits[:6]

            for item in IranianBank.objects.all():
                prefixes = item.card_prefixes or []

                if card_bin in prefixes:
                    bank = item
                    break

            if bank is None:
                return Response(
                    {
                        "fields": {
                            "cardNumber": "بانک صادرکننده این کارت شناسایی نشد."
                        }
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            account = BankAccount.objects.create(
                user=request.user,
                bank=bank,
                owner_name=owner_name,
                card_number=card_digits,
                iban=iban,
                account_number=account_number,
                status="pending",
                preferred=False,
            )

        except Exception:
            return Response(
                {"detail": "ثبت حساب بانکی انجام نشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BankAccountSerializer(account)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )



class BankAccountDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return BankAccount.objects.get(
                id=pk,
                user=request.user,
            )
        except BankAccount.DoesNotExist:
            return None

    def get(self, request, pk):
        account = self.get_object(request, pk)

        if account is None:
            return Response(
                {"detail": "Bank account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BankAccountSerializer(account)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        account = self.get_object(request, pk)

        if account is None:
            return Response(
                {"detail": "Bank account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        account.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class BankDetectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        card_bin = str(request.data.get("bin", ""))[:6]

        if len(card_bin) != 6 or not card_bin.isdigit():
            return Response(
                None,
                status=status.HTTP_200_OK,
            )

        for bank in IranianBank.objects.all():
            prefixes = bank.card_prefixes or []

            if card_bin in prefixes:
                serializer = IranianBankSerializer(bank)
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK,
                )

        return Response(
            None,
            status=status.HTTP_200_OK,
        )


class BankAccountPreferredAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            account = BankAccount.objects.get(id=pk, user=request.user)
            if account.status != "verified":
                return Response(
                    {"detail": "Only verified accounts can be preferred"},
                    status=status.HTTP_409_CONFLICT
                )
            # Set all other accounts to non-preferred
            BankAccount.objects.filter(user=request.user).update(preferred=False)
            account.preferred = True
            account.save()
            serializer = BankAccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BankAccount.DoesNotExist:
            return Response(
                {"detail": "Bank account not found"},
                status=status.HTTP_404_NOT_FOUND
            )
