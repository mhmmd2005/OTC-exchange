from django.urls import path

from .views import (
    BankAccountListCreateAPIView,
    BankAccountPreferredAPIView,
    BankDetectAPIView,
    DashboardSummaryAPIView,
    IranianBankListAPIView,
    UserPreferencesAPIView,
    UserProfileAPIView,
    BankAccountDetailAPIView
)

urlpatterns = [
    path(
        "users/me",
        UserProfileAPIView.as_view(),
        name="user-profile",
    ),
    path(
        "bank-accounts",
        BankAccountListCreateAPIView.as_view(),
        name="bank-account-list-create",
    ),
    path(
        "users/me/preferences",
        UserPreferencesAPIView.as_view(),
        name="user-preferences",
    ),
    path(
        "dashboard/summary",
        DashboardSummaryAPIView.as_view(),
        name="dashboard-summary",
    ),
    path(
        "banks",
        IranianBankListAPIView.as_view(),
        name="iranian-bank-list",
    ),
    path(
        "banks/detect",
        BankDetectAPIView.as_view(),
        name="bank-detect",
    ),
    path(
        "bank-accounts/<int:pk>",
        BankAccountDetailAPIView.as_view(),
        name="bank-account-detail",
    ),
    path(
        "bank-accounts/<int:pk>/preferred",
        BankAccountPreferredAPIView.as_view(),
        name="bank-account-preferred",
    ),
]
