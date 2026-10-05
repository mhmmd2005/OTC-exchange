from decimal import Decimal

from django.conf import settings
from django.db.models import Prefetch
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models import Asset, AssetNetwork
from apps.assets.serializers import AssetNetworkSerializer

from .models import Wallet
from .serializers import WalletSerializer


TOMAN_ASSET_SYMBOL = getattr(
    settings,
    "TOMAN_ASSET_SYMBOL",
    "IRT",
).upper()


def _serialize_decimal(value: Decimal) -> str:
    return format(value, "f")


def _build_wallet_asset(wallet: Wallet) -> dict:
    asset = wallet.asset

    total = wallet.balance
    available = wallet.available_balance
    locked = wallet.locked_balance

    # Conservative portfolio valuation:
    # value is based on the user's current sell price.
    toman_value = total * asset.sell_price_toman

    networks = AssetNetworkSerializer(
        asset.networks.all(),
        many=True,
    ).data

    return {
        "symbol": asset.symbol,
        "nameFa": asset.name_fa,
        "nameEn": asset.name,
        "iconUrl": asset.icon_url,
        "color": asset.color,
        "available": _serialize_decimal(available),
        "locked": _serialize_decimal(locked),
        "total": _serialize_decimal(total),
        "tomanValue": _serialize_decimal(toman_value),
        "buyEnabled": bool(asset.tradable),
        "sellEnabled": bool(asset.tradable),
        "depositEnabled": bool(asset.deposit_enabled),
        "withdrawalEnabled": bool(asset.withdrawal_enabled),
        "networks": networks,
    }


class WalletListAPIView(generics.ListAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Wallet.objects
            .filter(user=self.request.user)
            .select_related("asset")
            .order_by("asset__symbol")
        )


class WalletSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallets = (
            Wallet.objects
            .filter(user=request.user)
            .select_related("asset")
            .prefetch_related(
                Prefetch(
                    "asset__networks",
                    queryset=AssetNetwork.objects.all().order_by("code"),
                )
            )
            .order_by("asset__symbol")
        )

        assets = []

        toman_balance = Decimal("0")
        available_toman = Decimal("0")
        locked_toman = Decimal("0")
        crypto_value_toman = Decimal("0")

        for wallet in wallets:
            asset = wallet.asset

            total = wallet.balance
            available = wallet.available_balance
            locked = wallet.locked_balance

            if asset.symbol.upper() == TOMAN_ASSET_SYMBOL:
                toman_balance += total
                available_toman += available
                locked_toman += locked
            else:
                crypto_value_toman += (
                    total * asset.sell_price_toman
                )

            assets.append(_build_wallet_asset(wallet))

        total_value_toman = (
            toman_balance + crypto_value_toman
        )

        return Response({
            "totalValueToman": _serialize_decimal(total_value_toman),
            "tomanBalance": _serialize_decimal(toman_balance),
            "availableToman": _serialize_decimal(available_toman),
            "lockedToman": _serialize_decimal(locked_toman),
            "cryptoValueToman": _serialize_decimal(crypto_value_toman),
            "assets": assets,
            "updatedAt": timezone.now().isoformat(),
        })


class WalletAssetDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, symbol):
        symbol = symbol.upper()

        try:
            wallet = (
                Wallet.objects
                .select_related("asset")
                .prefetch_related(
                    Prefetch(
                        "asset__networks",
                        queryset=AssetNetwork.objects.all().order_by("code"),
                    )
                )
                .get(
                    user=request.user,
                    asset__symbol=symbol,
                )
            )
        except Wallet.DoesNotExist:
            return Response(
                {"detail": "Wallet not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(_build_wallet_asset(wallet))


class WalletAssetNetworksAPIView(APIView):
    permission_classes = [IsAuthenticated]

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

        networks = asset.networks.all().order_by("code")

        serializer = AssetNetworkSerializer(
            networks,
            many=True,
        )

        return Response(serializer.data)


class WalletDepositAddressAPIView(APIView):
    """
    Returns an already-provisioned deposit address.

    This endpoint NEVER creates a fake address.
    Address generation/provisioning will be connected to
    the crypto wallet provider later.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, symbol):
        symbol = symbol.upper()
        network_code = (
            request.query_params.get("network") or ""
        ).strip()

        if not network_code:
            return Response(
                {
                    "detail": (
                        "Network is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            wallet = (
                Wallet.objects
                .select_related("asset")
                .get(
                    user=request.user,
                    asset__symbol=symbol,
                )
            )
        except Wallet.DoesNotExist:
            return Response(
                {"detail": "Wallet not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not wallet.asset.deposit_enabled:
            return Response(
                {
                    "detail": (
                        "Deposits are disabled for this asset."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            wallet.network
            and wallet.network.upper() == network_code.upper()
            and wallet.deposit_address
        ):
            return Response({
                "symbol": wallet.asset.symbol,
                "network": network_code,
                "address": wallet.deposit_address,
            })

        return Response(
            {
                "detail": (
                    "Deposit address is not provisioned "
                    "for this network."
                )
            },
            status=status.HTTP_404_NOT_FOUND,
        )