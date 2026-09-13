from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import OTCQuote
from .serializers import OTCQuoteSerializer


class OTCQuoteCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import OTCQuote
        from apps.assets.models import Asset

        side = request.data.get("side")
        asset_symbol = request.data.get("assetSymbol")
        input_side = request.data.get("inputSide", "toman")
        amount = request.data.get("amount")

        try:
            asset = Asset.objects.get(symbol=asset_symbol.upper(), is_active=True)
        except Asset.DoesNotExist:
            return Response(
                {"detail": "Asset not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate quote (simplified - in production use real pricing)
        rate_toman = getattr(asset, "buy_price_toman" if side == "buy" else "sell_price_toman", 0)
        
        if input_side == "toman":
            toman_amount = float(amount)
            crypto_amount = toman_amount / float(rate_toman) if rate_toman else 0
        else:
            crypto_amount = float(amount)
            toman_amount = crypto_amount * float(rate_toman)

        fee_percent = 0.5  # 0.5% fee
        fee_toman = toman_amount * (fee_percent / 100)
        final_toman_amount = toman_amount - fee_toman if side == "sell" else toman_amount + fee_toman

        quote = OTCQuote.objects.create(
            user=request.user,
            asset=asset,
            side=side,
            input_side=input_side,
            requested_amount=amount,
            rate_toman=rate_toman,
            crypto_amount=crypto_amount,
            toman_amount=toman_amount,
            fee_toman=fee_toman,
            fee_percent=fee_percent,
            final_toman_amount=final_toman_amount,
            minimum_toman=100000,  # 100,000 toman minimum
            maximum_toman=100000000,  # 100,000,000 toman maximum
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        serializer = OTCQuoteSerializer(quote)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OTCQuoteDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OTCQuoteSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return OTCQuote.objects.filter(user=self.request.user)


class OTCOrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import OTCQuote
        from apps.orders.models import Order
        from apps.assets.models import Asset
        import uuid

        quote_id = request.data.get("quoteId")
        accepted_rate = request.data.get("acceptedRateToman")
        client_request_id = request.data.get("clientRequestId")

        try:
            quote = OTCQuote.objects.get(id=quote_id, user=request.user)
            if quote.status != "pending":
                return Response(
                    {"detail": "Quote is no longer valid"},
                    status=status.HTTP_409_CONFLICT
                )
            if quote.expires_at < timezone.now():
                quote.status = "expired"
                quote.save()
                return Response(
                    {"detail": "Quote has expired"},
                    status=status.HTTP_409_CONFLICT
                )
        except OTCQuote.DoesNotExist:
            return Response(
                {"detail": "Quote not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create order from quote
        order_number = f"OTC-{uuid.uuid4().hex[:12].upper()}"
        order = Order.objects.create(
            user=request.user,
            asset=quote.asset,
            side=quote.side,
            order_number=order_number,
            amount=quote.crypto_amount,
            price=quote.toman_amount,
            rate_toman=quote.rate_toman,
            fee_toman=quote.fee_toman,
            final_toman_amount=quote.final_toman_amount,
            status="pending_payment",
            payment_source=request.data.get("paymentSource", ""),
            destination=request.data.get("destination", ""),
        )

        # Mark quote as accepted
        quote.status = "accepted"
        quote.save()

        # Return the created order
        from apps.orders.serializers import OrderSerializer
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
