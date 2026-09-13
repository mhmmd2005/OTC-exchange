from django.urls import path

from .views import MarketListAPIView

urlpatterns = [
    path("", MarketListAPIView.as_view(), name="market-list"),
]