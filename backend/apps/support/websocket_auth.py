import hashlib
import json
import secrets
from functools import lru_cache

import redis

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services.session import is_session_valid
from apps.admin_panel.models import AdminSession, AdminUser

from .models import Ticket


WS_TICKET_TTL_SECONDS = 30

_CONSUME_SCRIPT = """
local value = redis.call('GET', KEYS[1])
if value then
    redis.call('DEL', KEYS[1])
end
return value
"""


@lru_cache(maxsize=1)
def _redis_client():
    return redis.Redis.from_url(
        settings.REDIS_CACHE_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def _ticket_key(token: str) -> str:
    digest = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    return f"support-ws-ticket:{digest}"


def issue_ws_ticket(
    *,
    actor_type: str,
    actor_id: int,
    session_id: str,
    ticket_id: int,
) -> str:
    """
    Create an opaque, short-lived WebSocket credential.
    The credential is bound to one actor and one support ticket.
    """
    token = secrets.token_urlsafe(32)

    payload = {
        "actor_type": actor_type,
        "actor_id": int(actor_id),
        "session_id": str(session_id),
        "ticket_id": int(ticket_id),
    }

    _redis_client().set(
        _ticket_key(token),
        json.dumps(payload, separators=(",", ":")),
        ex=WS_TICKET_TTL_SECONDS,
    )

    return token


def _consume_ws_ticket(token: str):
    """
    Atomically fetch and delete a credential.
    A credential cannot be used successfully twice.
    """
    if not token or len(token) > 200:
        return None

    raw_payload = _redis_client().eval(
        _CONSUME_SCRIPT,
        1,
        _ticket_key(token),
    )

    if not raw_payload:
        return None

    try:
        payload = json.loads(raw_payload)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def _admin_session_is_valid(
    *,
    admin_id: int,
    session_id: str,
) -> bool:
    now = timezone.now()

    session = (
        AdminSession.objects
        .select_related("admin")
        .filter(
            pk=session_id,
            admin_id=admin_id,
            revoked_at__isnull=True,
        )
        .first()
    )

    if session is None or not session.admin.is_active:
        return False

    idle_timeout = int(
        settings.JWT_IDLE_TIMEOUT_SECONDS
    )

    expired_by_time = session.expires_at <= now

    expired_by_idle = (
        idle_timeout > 0
        and (
            now - session.last_activity_at
        ).total_seconds() >= idle_timeout
    )

    if expired_by_time or expired_by_idle:
        session.revoked_at = now
        session.save(update_fields=["revoked_at"])
        return False

    return True


def authorize_support_socket(
    token: str,
    requested_ticket_id: int,
):
    """
    Consume the one-time credential, then re-check:
    - the requested ticket;
    - the actor's relationship to the ticket;
    - the active authentication session.
    """
    payload = _consume_ws_ticket(token)

    if not payload:
        return None

    try:
        actor_type = payload["actor_type"]
        actor_id = int(payload["actor_id"])
        ticket_id = int(payload["ticket_id"])
        session_id = str(payload["session_id"])
    except (KeyError, TypeError, ValueError):
        return None

    if ticket_id != int(requested_ticket_id):
        return None

    if not session_id:
        return None

    ticket = (
        Ticket.objects
        .filter(pk=ticket_id)
        .only("id", "user_id")
        .first()
    )

    if ticket is None:
        return None

    if actor_type == "user":
        if ticket.user_id != actor_id:
            return None

        user_exists = User.objects.filter(
            pk=actor_id,
            is_active=True,
        ).exists()

        if not user_exists:
            return None

        if not is_session_valid(
            session_id,
            user_id=actor_id,
            enforce_idle=True,
        ):
            return None

    elif actor_type == "admin":
        admin_exists = AdminUser.objects.filter(
            pk=actor_id,
            is_active=True,
        ).exists()

        if not admin_exists:
            return None

        if not _admin_session_is_valid(
            admin_id=actor_id,
            session_id=session_id,
        ):
            return None

    else:
        return None

    return {
        "actor_type": actor_type,
        "actor_id": actor_id,
        "ticket_id": ticket_id,
        "session_id": session_id,
    }


def socket_actor_is_valid(actor: dict) -> bool:
    """
    Re-check session validity during an established WebSocket connection.
    """
    if not actor:
        return False

    try:
        actor_type = actor["actor_type"]
        actor_id = int(actor["actor_id"])
        ticket_id = int(actor["ticket_id"])
        session_id = str(actor["session_id"])
    except (KeyError, TypeError, ValueError):
        return False

    if actor_type == "user":
        if not Ticket.objects.filter(
            pk=ticket_id,
            user_id=actor_id,
        ).exists():
            return False

        if not User.objects.filter(
            pk=actor_id,
            is_active=True,
        ).exists():
            return False

        return is_session_valid(
            session_id,
            user_id=actor_id,
            enforce_idle=True,
        )

    if actor_type == "admin":
        if not AdminUser.objects.filter(
            pk=actor_id,
            is_active=True,
        ).exists():
            return False

        return _admin_session_is_valid(
            admin_id=actor_id,
            session_id=session_id,
        )

    return False