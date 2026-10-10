from django.urls import path

from .views_toman import (
    TomanWithdrawalCreateAPIView,
    TomanWithdrawalEstimateAPIView,
)


urlpatterns = [
    path(
        "estimate/",
        TomanWithdrawalEstimateAPIView.as_view(),
        name="toman-withdrawal-estimate",
    ),
    path(
        "",
        TomanWithdrawalCreateAPIView.as_view(),
        name="toman-withdrawal-create",
    ),
]