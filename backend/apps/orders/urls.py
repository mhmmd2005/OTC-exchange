from django.urls import path

from .views import OrderCancelAPIView, OrderDetailAPIView, OrderListAPIView

urlpatterns = [
    path("", OrderListAPIView.as_view(), name="order-list"),
    path("<int:id>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("<int:id>/cancel", OrderCancelAPIView.as_view(), name="order-cancel"),
]
