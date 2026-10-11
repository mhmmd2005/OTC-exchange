import re

from django.db import transaction
from django.db.models import Count, Q
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.support.models import Ticket, TicketMessage

from ..authentication import AdminJWTAuthentication
from ..permissions import IsAdminAuthenticated
from ..serializers import (
    AdminTicketDetailSerializer,
    AdminTicketListSerializer,
    AdminTicketReplySerializer,
    AdminTicketStatusSerializer,
)


class AdminTicketPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "pageSize"
    max_page_size = 100


class AdminTicketListAPIView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAdminAuthenticated]

    def get(self, request):
        queryset = (
            Ticket.objects
            .select_related("user")
            .annotate(message_count=Count("messages"))
            .order_by("-updated_at", "-id")
        )

        status_filter = request.query_params.get(
            "status", ""
        ).strip()

        category_filter = request.query_params.get(
            "category", ""
        ).strip()

        priority_filter = request.query_params.get(
            "priority", ""
        ).strip()

        search = request.query_params.get(
            "search", ""
        ).strip()

        valid_statuses = {
            value for value, _ in Ticket.STATUS_CHOICES
        }
        valid_categories = {
            value for value, _ in Ticket.CATEGORY_CHOICES
        }
        valid_priorities = {
            value for value, _ in Ticket.PRIORITY_CHOICES
        }

        if status_filter and status_filter not in valid_statuses:
            return Response(
                {"detail": "فیلتر وضعیت معتبر نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if category_filter and category_filter not in valid_categories:
            return Response(
                {"detail": "فیلتر دسته‌بندی معتبر نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if priority_filter and priority_filter not in valid_priorities:
            return Response(
                {"detail": "فیلتر اولویت معتبر نیست."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if category_filter:
            queryset = queryset.filter(category=category_filter)

        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        if search:
            condition = (
                Q(subject__icontains=search)
                | Q(user__phone_number__icontains=search)
                | Q(user__full_name__icontains=search)
                | Q(user__email__icontains=search)
            )

            ticket_number = re.fullmatch(
                r"(?:TK-)?0*(\d+)",
                search,
                re.IGNORECASE,
            )

            if ticket_number:
                condition |= Q(
                    id=int(ticket_number.group(1))
                )

            queryset = queryset.filter(condition)

        paginator = AdminTicketPagination()
        page = paginator.paginate_queryset(
            queryset,
            request,
            view=self,
        )

        page_size = (
            paginator.get_page_size(request)
            or paginator.page_size
        )

        return Response(
            {
                "items": AdminTicketListSerializer(
                    page,
                    many=True,
                ).data,
                "total": paginator.page.paginator.count,
                "page": paginator.page.number,
                "pageSize": page_size,
            },
            status=status.HTTP_200_OK,
        )


class AdminTicketDetailAPIView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAdminAuthenticated]

    def get(self, request, pk):
        try:
            ticket = (
                Ticket.objects
                .select_related("user")
                .annotate(message_count=Count("messages"))
                .prefetch_related(
                    "messages__sender",
                    "messages__admin_sender",
                )
                .get(pk=pk)
            )
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "تیکت پیدا نشد."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            AdminTicketDetailSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )


class AdminTicketReplyAPIView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAdminAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        serializer = AdminTicketReplySerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        try:
            ticket = (
                Ticket.objects
                .select_for_update()
                .get(pk=pk)
            )
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "تیکت پیدا نشد."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ticket.status == "closed":
            return Response(
                {
                    "detail": (
                        "این تیکت بسته شده است. "
                        "ابتدا وضعیت آن را تغییر دهید."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        TicketMessage.objects.create(
            ticket=ticket,
            admin_sender=request.user,
            message=serializer.validated_data["body"],
        )

        # پاسخ ادمین برای کاربر به‌عنوان پاسخ داده‌شده نمایش داده می‌شود.
        ticket.status = "resolved"
        ticket.save(
            update_fields=["status", "updated_at"],
        )

        ticket = (
            Ticket.objects
            .select_related("user")
            .annotate(message_count=Count("messages"))
            .prefetch_related(
                "messages__sender",
                "messages__admin_sender",
            )
            .get(pk=pk)
        )

        return Response(
            AdminTicketDetailSerializer(ticket).data,
            status=status.HTTP_201_CREATED,
        )


class AdminTicketStatusAPIView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAdminAuthenticated]

    @transaction.atomic
    def patch(self, request, pk):
        serializer = AdminTicketStatusSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        try:
            ticket = (
                Ticket.objects
                .select_for_update()
                .get(pk=pk)
            )
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "تیکت پیدا نشد."},
                status=status.HTTP_404_NOT_FOUND,
            )

        ticket.status = serializer.validated_data["status"]
        ticket.save(
            update_fields=["status", "updated_at"],
        )

        ticket = (
            Ticket.objects
            .select_related("user")
            .annotate(message_count=Count("messages"))
            .prefetch_related(
                "messages__sender",
                "messages__admin_sender",
            )
            .get(pk=pk)
        )

        return Response(
            AdminTicketDetailSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )