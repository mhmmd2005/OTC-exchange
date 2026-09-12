from django.urls import path
from .views import (
    GetOrCreateKycAPIView,
    SubmitKycAPIView,
    UpdateKycAPIView,
    KycStatusAPIView,
    AdminKycListAPIView,
    AdminKycDetailAPIView,
    AdminKycApproveAPIView,
    AdminKycRejectAPIView,
)

urlpatterns = [
    path("", GetOrCreateKycAPIView.as_view(), name="kyc-get-or-create"),
    path("submit/", SubmitKycAPIView.as_view(), name="kyc-submit"),
    path("update/", UpdateKycAPIView.as_view(), name="kyc-update"),
    path("status/", KycStatusAPIView.as_view(), name="kyc-status"),
    path("admin/", AdminKycListAPIView.as_view(), name="kyc-admin-list"),
    path("admin/<int:pk>/", AdminKycDetailAPIView.as_view(), name="kyc-admin-detail"),
    path("admin/<int:pk>/approve/", AdminKycApproveAPIView.as_view(), name="kyc-admin-approve"),
    path("admin/<int:pk>/reject/", AdminKycRejectAPIView.as_view(), name="kyc-admin-reject"),

]
