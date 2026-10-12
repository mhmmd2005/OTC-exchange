from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .websocket_auth import (
    authorize_support_socket,
    socket_actor_is_valid,
)


@database_sync_to_async
def _authorize(token: str, ticket_id: int):
    return authorize_support_socket(token, ticket_id)


@database_sync_to_async
def _is_actor_valid(actor: dict) -> bool:
    return socket_actor_is_valid(actor)


class SupportTicketConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        try:
            self.ticket_id = int(
                self.scope["url_route"]["kwargs"]["ticket_id"]
            )
        except (KeyError, TypeError, ValueError):
            await self.close(code=4400)
            return

        query_string = (
            self.scope.get("query_string", b"")
            .decode("utf-8", errors="ignore")
        )
        query = parse_qs(query_string)
        token = query.get("ticket", [""])[0]

        if not token:
            await self.close(code=4401)
            return

        actor = await _authorize(
            token,
            self.ticket_id,
        )

        if not actor:
            await self.close(code=4403)
            return

        self.socket_actor = actor
        self.group_name = f"support_ticket_{self.ticket_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        await self.send_json(
            {
                "type": "connection.ready",
                "ticketId": self.ticket_id,
            }
        )

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)

        if group_name:
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        # WebSocket is deliberately read-only for chat messages.
        # Sending a message must go through the existing REST API.
        if not isinstance(content, dict):
            await self.close(code=4400)
            return

        if content.get("type") != "ping":
            await self.close(code=4400)
            return

        if not await _is_actor_valid(self.socket_actor):
            await self.close(code=4401)
            return

        await self.send_json({"type": "pong"})

    async def ticket_message(self, event):
        if not await _is_actor_valid(self.socket_actor):
            await self.close(code=4401)
            return

        await self.send_json(event["payload"])