from django.urls import path

from .views import WalletListAPIView

urlpatterns = [
    path("", WalletListAPIView.as_view(), name="wallet-list"),
]
