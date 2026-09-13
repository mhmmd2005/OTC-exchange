from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Asset, AssetNetwork
from .serializers import AssetSerializer, AssetNetworkSerializer


class AssetListAPIView(generics.ListAPIView):
    queryset = Asset.objects.filter(is_active=True)
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]


class AssetDetailAPIView(generics.RetrieveAPIView):
    queryset = Asset.objects.filter(is_active=True)
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]
    lookup_field = "symbol"


class AssetNetworkListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, symbol):
        try:
            asset = Asset.objects.get(symbol=symbol.upper(), is_active=True)
            networks = asset.networks.all()
            serializer = AssetNetworkSerializer(networks, many=True)
            return Response(serializer.data)
        except Asset.DoesNotExist:
            return Response(
                {"detail": "Asset not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class AssetPriceHistoryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, symbol):
        try:
            Asset.objects.get(symbol=symbol.upper(), is_active=True)
            # Return empty price history for now
            # In production, this would query a price history table
            return Response([])
        except Asset.DoesNotExist:
            return Response(
                {"detail": "Asset not found"},
                status=status.HTTP_404_NOT_FOUND
            )
