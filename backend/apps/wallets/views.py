from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Wallet
from .serializers import WalletSerializer


class WalletListAPIView(generics.ListAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [AllowAny]



class WalletSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallets = Wallet.objects.filter(
            user=request.user
        ).select_related("asset")

        assets = []

        for wallet in wallets:
            asset = wallet.asset
            total = wallet.balance
            available = wallet.available_balance
            locked = wallet.locked_balance

            assets.append({
                "symbol": asset.symbol,
                "nameFa": asset.name_fa,
                "nameEn": asset.name,
                "iconUrl": asset.icon_url,
                "color": asset.color,
                "available": str(available),
                "locked": str(locked),
                "total": str(total),
                "tomanValue": "0",
                "buyEnabled": asset.tradable,
                "sellEnabled": asset.tradable,
                "depositEnabled": asset.deposit_enabled,
                "withdrawalEnabled": asset.withdrawal_enabled,
                "networks": [],
            })

        return Response({
            "totalValueToman": "0",
            "tomanBalance": "0",
            "availableToman": "0",
            "lockedToman": "0",
            "cryptoValueToman": "0",
            "assets": assets,
            "updatedAt": timezone.now().isoformat(),
        })
