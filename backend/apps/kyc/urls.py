from django.urls import path
from .views import (
    GetOrCreateKycAPIView,
    SubmitKycAPIView,
    UpdateKycAPIView,
    KycStatusAPIView,
)

urlpatterns = [
    path("", GetOrCreateKycAPIView.as_view(), name="kyc-get-or-create"),
    path("submit/", SubmitKycAPIView.as_view(), name="kyc-submit"),
    path("update/", UpdateKycAPIView.as_view(), name="kyc-update"),
    path("status/", KycStatusAPIView.as_view(), name="kyc-status"),
]
