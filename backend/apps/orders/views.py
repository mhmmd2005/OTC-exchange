from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.kyc.permissions import IsKycVerified

from .models import Order
from .serializers import OrderSerializer


class OrderPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = "pageSize"
    page_query_param = "page"
    max_page_size = 100


class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = (
            Order.objects
            .filter(user=self.request.user)
            .order_by("-created_at")
        )

        side = self.request.query_params.get("side")
        status_filter = self.request.query_params.get("status")
        asset = self.request.query_params.get("asset")
        search = self.request.query_params.get("search")

        if side in {"buy", "sell"}:
            queryset = queryset.filter(side=side)

        if status_filter:
            if status_filter == "active":
                queryset = queryset.filter(
                    status__in=[
                        "pending_payment",
                        "payment_confirmed",
                        "processing",
                    ]
                )
            else:
                queryset = queryset.filter(
                    status=status_filter
                )

        if asset:
            queryset = queryset.filter(
                asset__symbol=asset
            )

        if search:
            queryset = queryset.filter(
                order_number__icontains=search
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
            )

            paginator = self.paginator

            return Response({
                "items": serializer.data,
                "page": paginator.page.number,
                "pageSize": (
                    paginator
                    .page
                    .paginator
                    .per_page
                ),
                "total": (
                    paginator
                    .page
                    .paginator
                    .count
                ),
                "totalPages": (
                    paginator
                    .page
                    .paginator
                    .num_pages
                ),
            })

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response({
            "items": serializer.data,
            "page": 1,
            "pageSize": len(
                serializer.data
            ),
            "total": len(
                serializer.data
            ),
            "totalPages": 1,
        })


class OrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        )


class OrderCancelAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsKycVerified,
    ]

    def post(self, request, id):
        try:
            order = Order.objects.get(
                id=id,
                user=request.user,
            )

            if order.status != "pending_payment":
                return Response(
                    {
                        "detail": (
                            "This order can no longer "
                            "be cancelled"
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            order.status = "cancelled"
            order.save()

            serializer = OrderSerializer(order)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Order.DoesNotExist:
            return Response(
                {
                    "detail": "Order not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )