from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import KycApplication
from .serializers import KycApplicationSerializer


class KycApplicationListAPIView(generics.ListAPIView):
    queryset = KycApplication.objects.all()
    serializer_class = KycApplicationSerializer
    permission_classes = [AllowAny]
