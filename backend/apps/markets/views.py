from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Market
from .serializers import MarketSerializer


class MarketListAPIView(generics.ListAPIView):
    serializer_class = MarketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Market.objects.select_related("asset").filter(is_active=True, asset__is_active=True).order_by(
            "asset__symbol")

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                asset__symbol__icontains=search
            ) | queryset.filter(
                asset__name_fa__icontains=search
            ) | queryset.filter(
                asset__name__icontains=search
            )

        return queryset


from django.shortcuts import render

# Create your views here.
