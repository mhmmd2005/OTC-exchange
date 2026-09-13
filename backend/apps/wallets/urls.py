from django.urls import path

from .views import WalletListAPIView, WalletSummaryAPIView

urlpatterns = [
    path("", WalletListAPIView.as_view(), name="wallet-list"),
    path("summary/", WalletSummaryAPIView.as_view(), name="wallet-summary"),
]
