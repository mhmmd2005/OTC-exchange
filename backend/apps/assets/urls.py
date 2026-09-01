from django.urls import path

from .views import AssetListAPIView

urlpatterns = [
    path("", AssetListAPIView.as_view(), name="asset-list"),
]
