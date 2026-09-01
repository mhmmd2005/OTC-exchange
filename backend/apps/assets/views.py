from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Asset
from .serializers import AssetSerializer


class AssetListAPIView(generics.ListAPIView):
    queryset = Asset.objects.filter(is_active=True)
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]
