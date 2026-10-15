import math

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification


FRONTEND_CATEGORIES = {
    "order",
    "deposit",
    "withdrawal",
    "verification",
    "security",
    "support",
    "system",
}


def wallet_keyword_query(words):
    query = Q()

    for word in words:
        query |= (
            Q(title__icontains=word)
            | Q(message__icontains=word)
            | Q(action_url__icontains=word)
        )

    return query


DEPOSIT_WORDS = ["واریز", "deposit"]
WITHDRAWAL_WORDS = ["برداشت", "withdrawal", "withdraw"]

WALLET_FINANCIAL_QUERY = (
    wallet_keyword_query(DEPOSIT_WORDS)
    | wallet_keyword_query(WITHDRAWAL_WORDS)
)


def public_category(notification):
    category = notification.category

    if category in FRONTEND_CATEGORIES:
        return category

    if category == "kyc":
        return "verification"

    if category == "wallet":
        text = " ".join([
            notification.title,
            notification.message,
            notification.action_url,
        ]).lower()

        if any(word in text for word in WITHDRAWAL_WORDS):
            return "withdrawal"

        if any(word in text for word in DEPOSIT_WORDS):
            return "deposit"

    return "system"


def notification_payload(notification):
    item = {
        "id": str(notification.pk),
        "category": public_category(notification),
        "title": notification.title,
        "message": notification.message,
        "read": notification.is_read,
        "createdAt": notification.created_at.isoformat(),
    }

    if notification.action_label and notification.action_url:
        item["action"] = {
            "label": notification.action_label,
            "to": notification.action_url,
        }

    return item


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Notification.objects.filter(
            user=request.user,
        ).order_by("-created_at", "-pk")

        category = request.query_params.get("category", "").strip()
        read_value = request.query_params.get("read")

        if category and category not in FRONTEND_CATEGORIES:
            return Response(
                {"detail": "Invalid notification category."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if read_value is not None:
            normalized_read = read_value.lower()

            if normalized_read in {"true", "1"}:
                queryset = queryset.filter(is_read=True)
            elif normalized_read in {"false", "0"}:
                queryset = queryset.filter(is_read=False)
            else:
                return Response(
                    {"detail": "Invalid read filter."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if category == "verification":
            queryset = queryset.filter(
                Q(category="verification") | Q(category="kyc")
            )
        elif category == "deposit":
            queryset = queryset.filter(
                Q(category="deposit")
                | (
                    Q(category="wallet")
                    & wallet_keyword_query(DEPOSIT_WORDS)
                )
            )
        elif category == "withdrawal":
            queryset = queryset.filter(
                Q(category="withdrawal")
                | (
                    Q(category="wallet")
                    & wallet_keyword_query(WITHDRAWAL_WORDS)
                )
            )
        elif category == "system":
            queryset = queryset.filter(
                Q(category="system")
                | (
                    Q(category="wallet")
                    & ~WALLET_FINANCIAL_QUERY
                )
            )
        elif category:
            queryset = queryset.filter(category=category)

        try:
            page = max(1, int(request.query_params.get("page", "1")))
        except (TypeError, ValueError):
            page = 1

        try:
            page_size = int(
                request.query_params.get("pageSize", "50")
            )
        except (TypeError, ValueError):
            page_size = 50

        page_size = min(100, max(1, page_size))

        total = queryset.count()
        total_pages = math.ceil(total / page_size)
        offset = (page - 1) * page_size

        notifications = queryset[offset:offset + page_size]

        return Response({
            "items": [
                notification_payload(item)
                for item in notifications
            ],
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": total_pages,
        })


class NotificationUnreadCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()

        return Response(count)


class NotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            user=request.user,
        )

        read_value = request.data.get("read", True)

        if not isinstance(read_value, bool):
            return Response(
                {"detail": "The read field must be a boolean."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification.is_read = read_value
        notification.read_at = (
            timezone.now() if read_value else None
        )

        notification.save(
            update_fields=["is_read", "read_at"]
        )

        return Response(notification_payload(notification))

    def delete(self, request, pk):
        notification = get_object_or_404(
            Notification,
            pk=pk,
            user=request.user,
        )

        notification.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationMarkAllReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        now = timezone.now()

        Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=now,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)