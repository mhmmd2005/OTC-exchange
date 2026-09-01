from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Trade
from .serializers import TradeSerializer


class TradeListAPIView(generics.ListAPIView):
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = [AllowAny]
