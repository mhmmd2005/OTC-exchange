from django.urls import path

from .views import (
    NotificationListAPIView,
    NotificationMarkAllReadAPIView,
    NotificationReadAPIView,
    NotificationUnreadCountAPIView,
)

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    path("unread-count", NotificationUnreadCountAPIView.as_view(), name="notification-unread-count"),
    path("<int:pk>", NotificationReadAPIView.as_view(), name="notification-detail"),
    path("read-all", NotificationMarkAllReadAPIView.as_view(), name="notification-read-all"),
]