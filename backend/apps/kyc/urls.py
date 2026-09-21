from django.urls import path

from .views import (
    GetOrCreateKycAPIView,
    KycStatusAPIView,
    SubmitBasicInfoAPIView,
    SubmitIdentityDocumentAPIView,

)

urlpatterns = [
    path("", GetOrCreateKycAPIView.as_view(), name="kyc-get-or-create"),
    path("basic-info", SubmitBasicInfoAPIView.as_view(), name="kyc-basic-info"),
    path("identity", SubmitIdentityDocumentAPIView.as_view(), name="kyc-identity"),
    path("status/", KycStatusAPIView.as_view(), name="kyc-status"),
]


