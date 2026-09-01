from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Wallet
from .serializers import WalletSerializer


class WalletListAPIView(generics.ListAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [AllowAny]
