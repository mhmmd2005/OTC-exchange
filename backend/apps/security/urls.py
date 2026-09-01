from django.urls import path

from .views import LoginHistoryListAPIView, SecurityEventListAPIView

urlpatterns = [
    path("events/", SecurityEventListAPIView.as_view(), name="security-event-list"),
    path("login-history/", LoginHistoryListAPIView.as_view(), name="login-history-list"),
]
