from django.urls import path

from .views import (
    AssetDetailAPIView,
    AssetListAPIView,
    AssetNetworkListAPIView,
    AssetPriceHistoryAPIView,
)

urlpatterns = [
    path("", AssetListAPIView.as_view(), name="asset-list"),
    path("<str:symbol>/", AssetDetailAPIView.as_view(), name="asset-detail"),
    path("<str:symbol>/networks/", AssetNetworkListAPIView.as_view(), name="asset-networks"),
    path("<str:symbol>/history/", AssetPriceHistoryAPIView.as_view(), name="asset-history"),
]
