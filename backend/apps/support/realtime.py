import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import TicketMessage


logger = logging.getLogger(__name__)


def broadcast_ticket_message(message_id: int) -> None:
    """
    Publish a persisted ticket message to all authorized subscribers
    of that ticket. REST remains the source of truth.
    """
    try:
        message = (
            TicketMessage.objects
            .select_related(
                "ticket",
                "sender",
                "admin_sender",
            )
            .get(pk=message_id)
        )

        ticket = message.ticket
        channel_layer = get_channel_layer()

        if channel_layer is None:
            return

        if message.admin_sender_id:
            sender = "support"
            sender_name = (
                message.admin_sender.full_name
                or message.admin_sender.email
            )
        else:
            sender = "user"
            sender_name = (
                message.sender.full_name
                or message.sender.phone_number
            )

        user_status = {
            "pending": "waiting_for_user",
            "resolved": "answered",
        }.get(ticket.status, ticket.status)

        payload = {
            "type": "message.created",
            "ticketId": ticket.pk,
            "message": {
                "id": message.pk,
                "sender": sender,
                "senderName": sender_name,
                "body": message.message,
                "createdAt": message.created_at.isoformat(),
            },
            "ticket": {
                "adminStatus": ticket.status,
                "userStatus": user_status,
                "updatedAt": ticket.updated_at.isoformat(),
                "messageCount": TicketMessage.objects.filter(
                    ticket_id=ticket.pk
                ).count(),
            },
        }

        async_to_sync(channel_layer.group_send)(
            f"support_ticket_{ticket.pk}",
            {
                "type": "ticket.message",
                "payload": payload,
            },
        )

    except Exception:
        # A realtime notification failure must not turn a successfully
        # persisted REST response into an HTTP error.
        logger.exception(
            "Failed to broadcast support ticket message %s",
            message_id,
        )