from django.urls import path

from .views import (
    WalletAssetDetailAPIView,
    WalletAssetNetworksAPIView,
    WalletDepositAddressAPIView,
    WalletListAPIView,
    WalletSummaryAPIView,
)

urlpatterns = [
    path(
        "",
        WalletSummaryAPIView.as_view(),
        name="wallet-summary",
    ),
    path(
        "list/",
        WalletListAPIView.as_view(),
        name="wallet-list",
    ),
    path(
        "<str:symbol>/",
        WalletAssetDetailAPIView.as_view(),
        name="wallet-asset-detail",
    ),
    path(
        "<str:symbol>/networks/",
        WalletAssetNetworksAPIView.as_view(),
        name="wallet-asset-networks",
    ),
    path(
        "<str:symbol>/deposit-address/",
        WalletDepositAddressAPIView.as_view(),
        name="wallet-deposit-address",
    ),
]