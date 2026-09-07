import json
import secrets
import time

from django.conf import settings
from django.core.cache import cache

SESSION_PREFIX = "auth-session:"
USER_VERSION_PREFIX = "auth-session-version:"


def session_key(session_id):
    return f"{SESSION_PREFIX}{session_id}"


def user_version_key(user_id):
    return f"{USER_VERSION_PREFIX}{user_id}"


def get_user_session_version(user_id):
    version = cache.get(user_version_key(user_id))

    if version is None:
        return 1

    return int(version)


def invalidate_all_user_sessions(user_id):
    current_version = get_user_session_version(user_id)
    new_version = current_version + 1

    cache.set(
        user_version_key(user_id),
        new_version,
        timeout=settings.JWT_REFRESH_DAYS * 86400,
    )

    return new_version


def create_session(user_id):
    session_id = secrets.token_urlsafe(32)
    current_time = int(time.time())
    session_version = get_user_session_version(user_id)

    session_data = {
        "user_id": int(user_id),
        "session_version": session_version,
        "last_activity": current_time,
    }

    cache.set(
        session_key(session_id),
        json.dumps(session_data),
        timeout=settings.JWT_REFRESH_DAYS * 86400,
    )

    return session_id


def get_session(session_id):
    data = cache.get(session_key(session_id))

    if not data:
        return None

    try:
        return json.loads(data)
    except (TypeError, ValueError, json.JSONDecodeError):
        cache.delete(session_key(session_id))
        return None


def is_session_valid(
        session_id,
        user_id=None,
        enforce_idle=True,
):
    session_data = get_session(session_id)

    if not session_data:
        return False

    if user_id is not None:
        if int(session_data.get("user_id", 0)) != int(user_id):
            return False

    stored_version = int(session_data.get("session_version", 1))
    current_version = get_user_session_version(
        session_data.get("user_id")
    )

    if stored_version != current_version:
        return False

    if enforce_idle:
        current_time = int(time.time())
        last_activity = int(
            session_data.get("last_activity", 0)
        )

        if (
                current_time - last_activity
                >= settings.JWT_IDLE_TIMEOUT_SECONDS
        ):
            delete_session(session_id)
            return False

    return True


def update_session(session_id, user_id=None):
    session_data = get_session(session_id)

    if not session_data:
        return False

    if user_id is not None:
        if int(session_data.get("user_id", 0)) != int(user_id):
            return False

    stored_version = int(
        session_data.get("session_version", 1)
    )

    current_version = get_user_session_version(
        session_data.get("user_id")
    )

    if stored_version != current_version:
        delete_session(session_id)
        return False

    current_time = int(time.time())
    last_activity = int(
        session_data.get("last_activity", 0)
    )

    if (
            current_time - last_activity
            >= settings.JWT_IDLE_TIMEOUT_SECONDS
    ):
        delete_session(session_id)
        return False

    session_data["last_activity"] = current_time

    cache.set(
        session_key(session_id),
        json.dumps(session_data),
        timeout=settings.JWT_REFRESH_DAYS * 86400,
    )

    return True


def delete_session(session_id):
    cache.delete(session_key(session_id))
