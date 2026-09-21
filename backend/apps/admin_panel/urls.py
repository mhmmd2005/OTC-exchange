from django.urls import path

from .views.auth import (
    AdminLoginAPIView,
    AdminLogoutAPIView,
    AdminMeAPIView,
    AdminRefreshAPIView,
)
from .views.kyc import (
    AdminKycApproveBankAPIView,
    AdminKycApproveStepAPIView,
    AdminKycDetailAPIView,
    AdminKycListAPIView,
    AdminKycRejectBankAPIView,
    AdminKycRejectStepAPIView,
)


urlpatterns = [
    path(
        "auth/login/",
        AdminLoginAPIView.as_view(),
        name="admin-login",
    ),
    path(
        "auth/refresh/",
        AdminRefreshAPIView.as_view(),
        name="admin-refresh",
    ),
    path(
        "auth/logout/",
        AdminLogoutAPIView.as_view(),
        name="admin-logout",
    ),
    path(
        "auth/me/",
        AdminMeAPIView.as_view(),
        name="admin-me",
    ),

    path(
        "kyc/",
        AdminKycListAPIView.as_view(),
        name="admin-kyc-list",
    ),
    path(
        "kyc/<int:pk>/",
        AdminKycDetailAPIView.as_view(),
        name="admin-kyc-detail",
    ),
    path(
        "kyc/<int:pk>/approve/<str:step>/",
        AdminKycApproveStepAPIView.as_view(),
        name="admin-kyc-approve-step",
    ),
    path(
        "kyc/<int:pk>/reject/<str:step>/",
        AdminKycRejectStepAPIView.as_view(),
        name="admin-kyc-reject-step",
    ),
    path(
        "kyc/<int:pk>/approve/bank/<int:bank_id>/",
        AdminKycApproveBankAPIView.as_view(),
        name="admin-kyc-approve-bank",
    ),
    path(
        "kyc/<int:pk>/reject/bank/<int:bank_id>/",
        AdminKycRejectBankAPIView.as_view(),
        name="admin-kyc-reject-bank",
    ),
]