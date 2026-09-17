from django.urls import path

from .views import (
    AdminKycApproveStepAPIView,
    AdminKycDetailAPIView,
    AdminKycListAPIView,
    AdminKycRejectStepAPIView,
    GetOrCreateKycAPIView,
    KycStatusAPIView,
    SubmitBasicInfoAPIView,
    SubmitIdentityDocumentAPIView,
    AdminKycApproveBankAPIView,
    AdminKycRejectBankAPIView,
)

urlpatterns = [
    path("", GetOrCreateKycAPIView.as_view(), name="kyc-get-or-create"),
    path("basic-info", SubmitBasicInfoAPIView.as_view(), name="kyc-basic-info"),
    path("identity", SubmitIdentityDocumentAPIView.as_view(), name="kyc-identity"),
    path("status/", KycStatusAPIView.as_view(), name="kyc-status"),
    path("admin/", AdminKycListAPIView.as_view(), name="kyc-admin-list"),
    path("admin/<int:pk>/", AdminKycDetailAPIView.as_view(), name="kyc-admin-detail"),
    path("admin/<int:pk>/approve/<str:step>/", AdminKycApproveStepAPIView.as_view(), name="kyc-admin-approve-step", ),
    path("admin/<int:pk>/reject/<str:step>/", AdminKycRejectStepAPIView.as_view(), name="kyc-admin-reject-step", ),
    path(
        "admin/<int:pk>/approve/bank/<int:bank_id>/",
        AdminKycApproveBankAPIView.as_view(),
        name="kyc-admin-approve-bank",
    ),
    path(
        "admin/<int:pk>/reject/bank/<int:bank_id>/",
        AdminKycRejectBankAPIView.as_view(),
        name="kyc-admin-reject-bank",
    ),
]
