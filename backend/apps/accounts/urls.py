from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginVerifyPasswordAPIView,
    MeAPIView,
    LogoutAPIView,
    RegistrationSetPasswordAPIView,
    RequestLoginOTPAPIView,
    RequestRegistrationOTPAPIView,
    VerifyOTPAPIView,
    RequestPasswordResetOTPAPIView,
    ResetPasswordAPIView,
)

urlpatterns = [
    path("request-login-otp/", RequestLoginOTPAPIView.as_view(), name="request-login-otp"),
    path("request-registration-otp/", RequestRegistrationOTPAPIView.as_view(), name="request-registration-otp"),
    path("verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),
    path("login/verify-password/", LoginVerifyPasswordAPIView.as_view(), name="login-verify-password"),
    path("register/set-password/", RegistrationSetPasswordAPIView.as_view(), name="register-set-password"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("me/", MeAPIView.as_view(), name="me"),
    path("request-password-reset-otp/", RequestPasswordResetOTPAPIView.as_view(), name="request-password-reset-otp"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
]
