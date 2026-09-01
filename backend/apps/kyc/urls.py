from django.urls import path

from .views import KycApplicationListAPIView

urlpatterns = [
    path("", KycApplicationListAPIView.as_view(), name="kyc-list"),
]
