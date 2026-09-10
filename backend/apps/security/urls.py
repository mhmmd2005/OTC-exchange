from django.urls import path

from .views import (
    SecurityOverviewAPIView,
    SecuritySessionsAPIView,
    SecuritySessionRevokeAPIView,
    SecurityOtherSessionsRevokeAPIView,
    SecurityEventListAPIView,
    LoginHistoryListAPIView,
    SecurityPasswordAPIView,
    TwoFactorSetupAPIView,
    TwoFactorAPIView,
    AntiPhishingAPIView,
    WithdrawalWhitelistAPIView,
)

urlpatterns = [
    path("", SecurityOverviewAPIView.as_view(), name="security-overview"),
    path("sessions/", SecuritySessionsAPIView.as_view(), name="security-sessions"),
    path("sessions/<str:session_id>/", SecuritySessionRevokeAPIView.as_view(), name="security-session-revoke"),
    path("sessions/others/", SecurityOtherSessionsRevokeAPIView.as_view(), name="security-other-sessions-revoke"),
    path("events/", SecurityEventListAPIView.as_view(), name="security-event-list"),
    path("login-history/", LoginHistoryListAPIView.as_view(), name="login-history-list"),
    path("password/", SecurityPasswordAPIView.as_view(), name="security-password"),
    path("two-factor/setup/", TwoFactorSetupAPIView.as_view(), name="two-factor-setup"),
    path("two-factor/", TwoFactorAPIView.as_view(), name="two-factor"),
    path("anti-phishing/", AntiPhishingAPIView.as_view(), name="anti-phishing"),
    path("withdrawal-whitelist/", WithdrawalWhitelistAPIView.as_view(), name="withdrawal-whitelist"),
]
