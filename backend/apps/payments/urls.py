from django.urls import path

from .views import (
    NexpalTomanDepositCallbackAPIView,
    TomanDepositCreateAPIView,
    TomanDepositDetailAPIView,
    TomanDepositTestPaymentAPIView,
)


urlpatterns = [
    path(
        "",
        TomanDepositCreateAPIView.as_view(),
        name="toman-deposit-create",
    ),
    path(
        "callback/",
        NexpalTomanDepositCallbackAPIView.as_view(),
        name="nexpal-toman-deposit-callback",
    ),
    path(
        "test-pay/<str:token>/",
        TomanDepositTestPaymentAPIView.as_view(),
        name="toman-deposit-test-payment",
    ),
    path(
        "<uuid:pk>/",
        TomanDepositDetailAPIView.as_view(),
        name="toman-deposit-detail",
    ),
]