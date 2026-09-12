from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = "pageSize"
    page_query_param = "page"
    max_page_size = 100


class TransactionListAPIView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = TransactionPagination

    def get_queryset(self):
        return Transaction.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginator = self.paginator
            return Response({
                "items": serializer.data,
                "total": paginator.page.paginator.count,
                "totalPages": paginator.page.paginator.num_pages,
                "page": paginator.page.number,
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "items": serializer.data,
            "total": len(serializer.data),
            "totalPages": 1,
            "page": 1,
        })
