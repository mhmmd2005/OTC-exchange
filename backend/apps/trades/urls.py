from django.urls import path

from .views import TradeListAPIView

urlpatterns = [
    path("", TradeListAPIView.as_view(), name="trade-list"),
]
