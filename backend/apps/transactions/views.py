from datetime import datetime, time

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from rest_framework import generics
from rest_framework.exceptions import ValidationError
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
        queryset = (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related("asset")
            .order_by("-created_at")
        )

        params = self.request.query_params

        transaction_type = (
            params.get("type") or ""
        ).strip().lower()

        transaction_status = (
            params.get("status") or ""
        ).strip().lower()

        asset_symbol = (
            params.get("asset") or ""
        ).strip().upper()

        network = (
            params.get("network") or ""
        ).strip()

        search = (
            params.get("search") or ""
        ).strip()

        from_value = (
            params.get("from") or ""
        ).strip()

        to_value = (
            params.get("to") or ""
        ).strip()

        if transaction_type:
            valid_types = {
                value
                for value, _ in Transaction.TYPE_CHOICES
            }

            if transaction_type not in valid_types:
                raise ValidationError({
                    "type": "Invalid transaction type."
                })

            queryset = queryset.filter(
                transaction_type=transaction_type
            )

        if transaction_status:
            valid_statuses = {
                value
                for value, _ in Transaction.STATUS_CHOICES
            }

            if transaction_status not in valid_statuses:
                raise ValidationError({
                    "status": "Invalid transaction status."
                })

            queryset = queryset.filter(
                status=transaction_status
            )

        if asset_symbol:
            queryset = queryset.filter(
                asset__symbol=asset_symbol
            )

        if network:
            queryset = queryset.filter(
                network_code__iexact=network
            )

        if search:
            queryset = queryset.filter(
                Q(reference_number__icontains=search)
                | Q(txid__icontains=search)
                | Q(order_id__icontains=search)
                | Q(title__icontains=search)
                | Q(description__icontains=search)
            )

        if from_value:
            queryset = self._apply_date_filter(
                queryset,
                from_value,
                is_from=True,
            )

        if to_value:
            queryset = self._apply_date_filter(
                queryset,
                to_value,
                is_from=False,
            )

        return queryset

    @staticmethod
    def _apply_date_filter(
        queryset,
        value,
        *,
        is_from,
    ):
        parsed_datetime = parse_datetime(
            value
        )

        if parsed_datetime is not None:
            if timezone.is_naive(
                parsed_datetime
            ):
                parsed_datetime = (
                    timezone.make_aware(
                        parsed_datetime
                    )
                )

            if is_from:
                return queryset.filter(
                    created_at__gte=parsed_datetime
                )

            return queryset.filter(
                created_at__lte=parsed_datetime
            )

        parsed_date = parse_date(value)

        if parsed_date is None:
            raise ValidationError({
                "date": (
                    "Invalid date. Use YYYY-MM-DD "
                    "or ISO 8601 datetime."
                )
            })

        if is_from:
            start = timezone.make_aware(
                datetime.combine(
                    parsed_date,
                    time.min,
                )
            )

            return queryset.filter(
                created_at__gte=start
            )

        end = timezone.make_aware(
            datetime.combine(
                parsed_date,
                time.max,
            )
        )

        return queryset.filter(
            created_at__lte=end
        )

    def list(
        self,
        request,
        *args,
        **kwargs,
    ):
        queryset = self.filter_queryset(
            self.get_queryset()
        )

        page = self.paginate_queryset(
            queryset
        )

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
            )

            paginator = self.paginator

            return Response({
                "items": serializer.data,
                "total": (
                    paginator.page
                    .paginator.count
                ),
                "totalPages": (
                    paginator.page
                    .paginator.num_pages
                ),
                "page": (
                    paginator.page.number
                ),
            })

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response({
            "items": serializer.data,
            "total": len(serializer.data),
            "totalPages": 1,
            "page": 1,
        })


class TransactionDetailAPIView(
    generics.RetrieveAPIView
):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related("asset")
        )

    lookup_field = "pk"