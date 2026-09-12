from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Ticket, TicketMessage
from .serializers import (
    CreateTicketMessageSerializer,
    CreateTicketSerializer,
    TicketMessageSerializer,
    TicketSerializer,
)


class FAQListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([], status=status.HTTP_200_OK)


class TicketDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            ticket = Ticket.objects.prefetch_related("messages").get(
                id=pk,
                user=request.user,
            )
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "Ticket not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TicketSerializer(
            ticket,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class TicketListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Ticket.objects.filter(
            user=request.user
        ).prefetch_related("messages")

        status_value = request.query_params.get("status")
        category = request.query_params.get("category")
        search = request.query_params.get("search")

        if status_value:
            queryset = queryset.filter(status=status_value)

        if category:
            queryset = queryset.filter(category=category)

        if search:
            queryset = queryset.filter(subject__icontains=search)

        serializer = TicketSerializer(
            queryset,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "item":serializer.data,
                "total": queryset.count(),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = CreateTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket = Ticket.objects.create(
            user=request.user,
            subject=serializer.validated_data["subject"].strip(),
            category=serializer.validated_data["category"],
            status="open",
        )

        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=serializer.validated_data["body"].strip(),
        )

        ticket = Ticket.objects.prefetch_related("messages").get(
            id=ticket.id
        )

        response_serializer = TicketSerializer(
            ticket,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class TicketMessageCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = CreateTicketMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ticket = Ticket.objects.get(
                id=pk,
                user=request.user,
            )
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "Ticket not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ticket.status == "closed":
            return Response(
                {"detail": "This ticket is closed"},
                status=status.HTTP_409_CONFLICT,
            )

        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=serializer.validated_data["body"].strip(),
        )

        ticket.status = "open"
        ticket.save(update_fields=["status", "updated_at"])

        response_serializer = TicketMessageSerializer(
            message,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class TicketCloseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            ticket = Ticket.objects.get(
                id=pk,
                user=request.user,
            )
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "Ticket not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        ticket.status = "closed"
        ticket.save(update_fields=["status", "updated_at"])

        ticket = Ticket.objects.prefetch_related("messages").get(
            id=ticket.id
        )

        serializer = TicketSerializer(
            ticket,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
