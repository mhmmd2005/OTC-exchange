from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import LoginHistory, SecurityEvent
from .serializers import LoginHistorySerializer, SecurityEventSerializer


class SecurityEventListAPIView(generics.ListAPIView):
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    permission_classes = [AllowAny]


class LoginHistoryListAPIView(generics.ListAPIView):
    queryset = LoginHistory.objects.all()
    serializer_class = LoginHistorySerializer
    permission_classes = [AllowAny]
