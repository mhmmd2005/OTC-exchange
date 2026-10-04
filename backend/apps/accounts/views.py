import jdatetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.models import BankAccount, BankCardPrefix, BankVerificationObservation, IranianBank
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
    UserSerializer,
    TwoFactorLoginSerializer,
)
from apps.accounts.serializers import (
    UserProfileSerializer,
    EmailVerificationSerializer,
    EmailVerificationService
)
from apps.accounts.services.auth import AuthService
from apps.accounts.services.bank_registry import (
    create_bank_verification_observation,
    find_bank_by_card,
    find_bank_by_iban,
    get_iban_bank_code,
    is_valid_card_number,
    is_valid_iranian_iban,
    normalize_card,
    normalize_iban,
)
from apps.accounts.services.session import (
    delete_session,
    update_session,
)
from apps.kyc.models import KycApplication
from apps.kyc.services.ehraz import EhrazAPIError, EhrazService

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


class LoginVerifyTwoFactorAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TwoFactorLoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            result = AuthService.verify_login_two_factor(
                two_factor_token=(
                    serializer.validated_data[
                        "two_factor_token"
                    ]
                ),
                code=serializer.validated_data[
                    "code"
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
                {
                    "detail": str(exc),
                },
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
        banks = IranianBank.objects.filter(is_active=True)
        serializer = IranianBankSerializer(banks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BankAccountListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = (
            BankAccount.objects
            .filter(
                user=request.user,
            )
            .select_related("bank")
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
            request.data.get(
                "cardNumber",
                "",
            ),
        )

        iban = str(
            request.data.get(
                "iban",
                "",
            ),
        )

        account_number = str(
            request.data.get(
                "accountNumber",
                "",
            ),
        )

        card_digits = normalize_card(
            card_number,
        )

        iban_value = normalize_iban(
            iban,
        )

        try:
            kyc = KycApplication.objects.get(
                user=request.user,
            )
        except KycApplication.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "ابتدا باید احراز هویت خود را تکمیل کنید."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        if not kyc.both_identity_steps_approved:
            return Response(
                {
                    "detail": (
                        "ابتدا باید اطلاعات هویتی و مدرک شناسایی "
                        "توسط ادمین تأیید شوند."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        if not settings.EHRAZ_API_TOKEN:
            return Response(
                {
                    "detail": (
                        "سرویس احراز هویت هنوز پیکربندی نشده است."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not kyc.national_id or not kyc.birth_date:
            return Response(
                {
                    "detail": (
                        "اطلاعات هویتی لازم برای بررسی حساب بانکی کامل نیست."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        owner_name = (
            f"{kyc.first_name} {kyc.last_name}"
        ).strip()

        if not owner_name:
            return Response(
                {
                    "detail": (
                        "نام و نام خانوادگی تأییدشده احراز هویت "
                        "در دسترس نیست."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        card_luhn_valid = is_valid_card_number(card_digits)
        iban_valid = is_valid_iranian_iban(iban_value)
        card_bank = find_bank_by_card(card_digits)
        iban_bank = find_bank_by_iban(iban_value)

        if not card_luhn_valid:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=False,
                iban_checksum_valid=iban_valid,
                card_bank_known=card_bank is not None,
                iban_bank_known=iban_bank is not None,
                banks_match=bool(card_bank and iban_bank and card_bank.pk == iban_bank.pk),
                result=BankVerificationObservation.RESULT_INVALID_CARD,
                failure_reason="card_luhn_invalid",
            )
            return Response(
                {
                    "fields": {
                        "cardNumber": (
                            "شماره کارت معتبر نیست."
                        )
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if not iban_valid:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=False,
                card_bank_known=card_bank is not None,
                iban_bank_known=iban_bank is not None,
                banks_match=bool(card_bank and iban_bank and card_bank.pk == iban_bank.pk),
                result=BankVerificationObservation.RESULT_INVALID_IBAN,
                failure_reason="iban_checksum_invalid",
            )
            return Response(
                {
                    "fields": {
                        "iban": (
                            "شماره شبا معتبر نیست."
                        )
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if card_bank is None and card_digits:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=False,
                iban_bank_known=iban_bank is not None,
                banks_match=bool(iban_bank and card_bank and card_bank.pk == iban_bank.pk),
                result=BankVerificationObservation.RESULT_UNKNOWN_CARD_PREFIX,
                failure_reason="card_prefix_unknown",
                observed_card_prefix=card_digits[:10],
            )

        if iban_bank is None:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=False,
                banks_match=False,
                result=BankVerificationObservation.RESULT_UNKNOWN_IBAN_BANK,
                failure_reason="iban_bank_unknown",
            )
            return Response(
                {
                    "fields": {
                        "iban": (
                            "بانک مربوط به شماره شبا "
                            "شناسایی نشد."
                        )
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if card_bank is not None and iban_bank.pk != card_bank.pk:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=True,
                iban_bank_known=True,
                banks_match=False,
                result=BankVerificationObservation.RESULT_BANK_MISMATCH,
                failure_reason="card_iban_bank_mismatch",
            )
            return Response(
                {
                    "fields": {
                        "iban": (
                            "بانک شماره کارت و شماره شبا "
                            "با یکدیگر مطابقت ندارند."
                        )
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        bank = card_bank if card_bank is not None else iban_bank

        # ---------------------------------------------------------
        # Duplicate card
        # ---------------------------------------------------------
        if BankAccount.objects.filter(
                card_number=card_digits,
        ).exists():
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=True,
                banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
                result=BankVerificationObservation.RESULT_DUPLICATE_CARD,
                failure_reason="duplicate_card",
            )
            return Response(
                {
                    "fields": {
                        "cardNumber": (
                            "این شماره کارت قبلاً ثبت شده است."
                        )
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # ---------------------------------------------------------
        # Duplicate IBAN
        # ---------------------------------------------------------
        if BankAccount.objects.filter(
                iban=iban_value,
        ).exists():
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=True,
                banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
                result=BankVerificationObservation.RESULT_DUPLICATE_IBAN,
                failure_reason="duplicate_iban",
            )
            return Response(
                {
                    "fields": {
                        "iban": (
                            "این شماره شبا قبلاً ثبت شده است."
                        )
                    }
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # ---------------------------------------------------------
        # Gregorian → Jalali YYYYMMDD
        # ---------------------------------------------------------
        birth_date = (
            jdatetime.date
            .fromgregorian(
                date=kyc.birth_date,
            )
            .strftime("%Y%m%d")
        )

        # ---------------------------------------------------------
        # Ehraz: IBAN ownership
        # ---------------------------------------------------------
        try:
            ehraz_result = (
                EhrazService.match_iban_with_national(
                    iban=iban_value,
                    national_code=kyc.national_id,
                    birth_date=birth_date,
                )
            )
        except EhrazAPIError as exc:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=True,
                banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
                result=BankVerificationObservation.RESULT_OWNERSHIP_UNAVAILABLE,
                failure_reason="ehraz_iban_unavailable",
            )
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if "matched" not in ehraz_result:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=True,
                banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
                result=BankVerificationObservation.RESULT_OWNERSHIP_UNAVAILABLE,
                failure_reason="ehraz_iban_response_incomplete",
            )
            return Response(
                {
                    "detail": (
                        "پاسخ سرویس احراز مالکیت حساب بانکی کامل نیست."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if ehraz_result["matched"] is not True:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=True,
                banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
                card_ownership_verified=False,
                iban_ownership_verified=False,
                result=BankVerificationObservation.RESULT_OWNERSHIP_FAILED,
                failure_reason="ehraz_iban_mismatch",
            )
            return Response(
                {
                    "detail": (
                        "اطلاعات حساب بانکی با اطلاعات هویتی "
                        "شما مطابقت ندارد."
                    )
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # ---------------------------------------------------------
        # Ehraz: Card ownership
        # ---------------------------------------------------------
        try:
            card_result = (
                EhrazService.match_card_with_national(
                    card_number=card_digits,
                    national_code=kyc.national_id,
                    birth_date=birth_date,
                )
            )
        except EhrazAPIError as exc:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=True,
                banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
                card_ownership_verified=False,
                iban_ownership_verified=True,
                result=BankVerificationObservation.RESULT_OWNERSHIP_UNAVAILABLE,
                failure_reason="ehraz_card_unavailable",
            )
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if "matched" not in card_result:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=True,
                banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
                card_ownership_verified=False,
                iban_ownership_verified=True,
                result=BankVerificationObservation.RESULT_OWNERSHIP_UNAVAILABLE,
                failure_reason="ehraz_card_response_incomplete",
            )
            return Response(
                {
                    "detail": (
                        "پاسخ سرویس احراز مالکیت کارت کامل نیست."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if card_result["matched"] is not True:
            create_bank_verification_observation(
                user=request.user,
                card_number=card_digits,
                iban=iban_value,
                card_luhn_valid=True,
                iban_checksum_valid=True,
                card_bank_known=card_bank is not None,
                iban_bank_known=True,
                banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
                card_ownership_verified=False,
                iban_ownership_verified=True,
                result=BankVerificationObservation.RESULT_OWNERSHIP_FAILED,
                failure_reason="ehraz_card_mismatch",
            )
            return Response(
                {
                    "detail": (
                        "اطلاعات کارت با اطلاعات هویتی "
                        "شما مطابقت ندارد."
                    )
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # ---------------------------------------------------------
        # Create verified bank account
        # ---------------------------------------------------------
        account = BankAccount.objects.create(
            user=request.user,
            bank=bank,
            owner_name=owner_name,
            card_number=card_digits,
            iban=iban_value,
            account_number=account_number,
            status="verified",
            preferred=False,
            verified_at=timezone.now(),
        )

        create_bank_verification_observation(
            user=request.user,
            card_number=card_digits,
            iban=iban_value,
            card_luhn_valid=True,
            iban_checksum_valid=True,
            card_bank_known=card_bank is not None,
            iban_bank_known=True,
            banks_match=bool(card_bank and card_bank.pk == iban_bank.pk),
            card_ownership_verified=True,
            iban_ownership_verified=True,
            result=BankVerificationObservation.RESULT_VERIFIED,
            failure_reason="",
        )

        kyc.sync_status()

        serializer = BankAccountSerializer(
            account,
        )

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
        value = str(
            request.data.get("bin", "")
        )

        bank = find_bank_by_card(value)

        if bank is None:
            return Response(
                None,
                status=status.HTTP_200_OK,
            )

        serializer = IranianBankSerializer(
            bank,
        )

        return Response(
            serializer.data,
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


class RequestPhoneVerificationOTPAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {
                    "detail": (
                        "Authentication is required."
                    )
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        phone_number = request.user.phone_number

        result = AuthService.request_otp(
            phone_number,
            purpose="phone_verification",
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


class VerifyPhoneVerificationOTPAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
                user=request.user,
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


class EmailVerificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = EmailVerificationService.verify(
                request.user,
                serializer.validated_data["token"],
            )
        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_200_OK,
        )
