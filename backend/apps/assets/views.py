from django.db.models import Prefetch

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Asset, AssetNetwork
from .serializers import (
    AssetNetworkSerializer,
    AssetSerializer,
)


class AssetListAPIView(generics.ListAPIView):
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            Asset.objects
            .filter(is_active=True)
            .prefetch_related(
                Prefetch(
                    "networks",
                    queryset=AssetNetwork.objects.all().order_by("code"),
                )
            )
            .order_by("symbol")
        )


class AssetDetailAPIView(generics.RetrieveAPIView):
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]
    lookup_field = "symbol"

    def get_queryset(self):
        return (
            Asset.objects
            .filter(is_active=True)
            .prefetch_related(
                Prefetch(
                    "networks",
                    queryset=AssetNetwork.objects.all().order_by("code"),
                )
            )
        )


class AssetNetworkListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, symbol):
        symbol = symbol.upper()

        try:
            asset = Asset.objects.get(
                symbol=symbol,
                is_active=True,
            )
        except Asset.DoesNotExist:
            return Response(
                {"detail": "Asset not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        networks = (
            AssetNetwork.objects
            .filter(asset=asset)
            .order_by("code")
        )

        serializer = AssetNetworkSerializer(
            networks,
            many=True,
        )

        return Response(serializer.data)


class AssetPriceHistoryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, symbol):
        symbol = symbol.upper()

        exists = Asset.objects.filter(
            symbol=symbol,
            is_active=True,
        ).exists()

        if not exists:
            return Response(
                {"detail": "Asset not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Price history endpoint will be connected
        # to the real price-history source later.
        return Response([])