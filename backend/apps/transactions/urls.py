from django.urls import path

from .views import (
    TransactionDetailAPIView,
    TransactionListAPIView,
)


urlpatterns = [
    path(
        "",
        TransactionListAPIView.as_view(),
        name="transaction-list",
    ),
    path(
        "<int:pk>/",
        TransactionDetailAPIView.as_view(),
        name="transaction-detail",
    ),
]