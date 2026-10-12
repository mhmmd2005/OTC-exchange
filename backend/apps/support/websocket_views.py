from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.accounts.authentication import IdleTimeoutJWTAuthentication
from apps.admin_panel.authentication import AdminJWTAuthentication
from apps.admin_panel.permissions import IsAdminAuthenticated

from .models import Ticket
from .websocket_auth import (
    WS_TICKET_TTL_SECONDS,
    issue_ws_ticket,
)


class UserSupportWebSocketTicketAPIView(APIView):
    authentication_classes = [IdleTimeoutJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        ticket = Ticket.objects.filter(
            pk=pk,
            user=request.user,
        ).only("id").first()

        if ticket is None:
            return Response(
                {"detail": "Ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        session_id = request.auth.get("session_id")

        if not session_id:
            return Response(
                {"detail": "A valid user session is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = issue_ws_ticket(
            actor_type="user",
            actor_id=request.user.pk,
            session_id=session_id,
            ticket_id=ticket.pk,
        )

        return Response(
            {
                "ticket": token,
                "expiresIn": WS_TICKET_TTL_SECONDS,
            },
            status=status.HTTP_200_OK,
        )


class AdminSupportWebSocketTicketAPIView(APIView):
    authentication_classes = [AdminJWTAuthentication]
    permission_classes = [IsAdminAuthenticated]

    def post(self, request, pk):
        ticket = Ticket.objects.filter(
            pk=pk,
        ).only("id").first()

        if ticket is None:
            return Response(
                {"detail": "Ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        session_id = request.auth.get("session_id")

        if not session_id:
            return Response(
                {"detail": "A valid admin session is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = issue_ws_ticket(
            actor_type="admin",
            actor_id=request.user.pk,
            session_id=session_id,
            ticket_id=ticket.pk,
        )

        return Response(
            {
                "ticket": token,
                "expiresIn": WS_TICKET_TTL_SECONDS,
            },
            status=status.HTTP_200_OK,
        )