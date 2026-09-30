import json
import secrets
import time

from django.conf import settings
from django.core.cache import cache


SESSION_PREFIX = "auth-session:"
USER_VERSION_PREFIX = "auth-session-version:"
USER_SESSIONS_PREFIX = "auth-user-sessions:"


def session_key(session_id):
    return f"{SESSION_PREFIX}{session_id}"


def user_version_key(user_id):
    return f"{USER_VERSION_PREFIX}{user_id}"


def user_sessions_key(user_id):
    return f"{USER_SESSIONS_PREFIX}{user_id}"


def get_user_session_version(user_id):
    version = cache.get(
        user_version_key(user_id)
    )

    if version is None:
        return 1

    return int(version)


def invalidate_all_user_sessions(user_id):
    current_version = get_user_session_version(
        user_id
    )

    new_version = current_version + 1

    cache.set(
        user_version_key(user_id),
        new_version,
        timeout=settings.JWT_REFRESH_DAYS * 86400,
    )

    return new_version


def _get_user_session_ids(user_id):
    data = cache.get(
        user_sessions_key(user_id),
        [],
    )

    if not isinstance(data, list):
        return []

    return [
        str(session_id)
        for session_id in data
        if session_id
    ]


def _save_user_session_ids(
    user_id,
    session_ids,
):
    unique_ids = list(
        dict.fromkeys(
            str(session_id)
            for session_id in session_ids
            if session_id
        )
    )

    cache.set(
        user_sessions_key(user_id),
        unique_ids,
        timeout=settings.JWT_REFRESH_DAYS * 86400,
    )


def _add_session_to_user_index(
    user_id,
    session_id,
):
    session_ids = _get_user_session_ids(
        user_id
    )

    if session_id not in session_ids:
        session_ids.append(
            session_id
        )

    _save_user_session_ids(
        user_id,
        session_ids,
    )


def _remove_session_from_user_index(
    user_id,
    session_id,
):
    session_ids = _get_user_session_ids(
        user_id
    )

    session_ids = [
        item
        for item in session_ids
        if item != str(session_id)
    ]

    _save_user_session_ids(
        user_id,
        session_ids,
    )


def parse_user_agent(user_agent):
    user_agent = (
        str(user_agent or "")
        .strip()
    )

    if not user_agent:
        return {
            "browser": "مرورگر",
            "os": "نامشخص",
            "device_type": "desktop",
            "device_name": "مرورگر",
        }

    # Browser
    if "SamsungBrowser/" in user_agent:
        browser = "Samsung Internet"
    elif "Edg/" in user_agent:
        browser = "Edge"
    elif "OPR/" in user_agent:
        browser = "Opera"
    elif "Firefox/" in user_agent:
        browser = "Firefox"
    elif "Chrome/" in user_agent:
        browser = "Chrome"
    elif "Safari/" in user_agent:
        browser = "Safari"
    else:
        browser = "مرورگر"

    # OS
    if "iPhone" in user_agent:
        operating_system = "iOS"
    elif "iPad" in user_agent:
        operating_system = "iOS"
    elif "Android" in user_agent:
        operating_system = "Android"
    elif "Windows" in user_agent:
        operating_system = "Windows"
    elif "Mac OS X" in user_agent:
        operating_system = "macOS"
    elif "Linux" in user_agent:
        operating_system = "Linux"
    else:
        operating_system = "نامشخص"

    # Device type
    if "iPad" in user_agent:
        device_type = "tablet"
    elif "Android" in user_agent:
        if "Mobile" in user_agent:
            device_type = "mobile"
        else:
            device_type = "tablet"
    elif "iPhone" in user_agent:
        device_type = "mobile"
    else:
        device_type = "desktop"

    if operating_system == "نامشخص":
        device_name = browser
    else:
        device_name = (
            f"{browser} در {operating_system}"
        )

    return {
        "browser": browser,
        "os": operating_system,
        "device_type": device_type,
        "device_name": device_name,
    }


def create_session(
    user_id,
    ip_address=None,
    user_agent="",
):
    session_id = secrets.token_urlsafe(32)
    current_time = int(time.time())
    session_version = get_user_session_version(
        user_id
    )

    parsed_user_agent = parse_user_agent(
        user_agent
    )

    session_data = {
        "user_id": int(user_id),
        "session_version": session_version,
        "created_at": current_time,
        "last_activity": current_time,
        "ip_address": ip_address,
        "user_agent": str(
            user_agent or ""
        )[:1000],
        "browser": parsed_user_agent["browser"],
        "os": parsed_user_agent["os"],
        "device_type": parsed_user_agent["device_type"],
        "device_name": parsed_user_agent["device_name"],
        "approximate_location": None,
    }

    cache.set(
        session_key(session_id),
        json.dumps(session_data),
        timeout=settings.JWT_REFRESH_DAYS * 86400,
    )

    _add_session_to_user_index(
        user_id,
        session_id,
    )

    return session_id


def get_session(session_id):
    if not session_id:
        return None

    data = cache.get(
        session_key(session_id)
    )

    if not data:
        return None

    try:
        if isinstance(data, bytes):
            data = data.decode("utf-8")

        if isinstance(data, str):
            return json.loads(data)

        if isinstance(data, dict):
            return data

        return None

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        cache.delete(
            session_key(session_id)
        )

        return None


def is_session_valid(
    session_id,
    user_id=None,
    enforce_idle=True,
):
    session_data = get_session(
        session_id
    )

    if not session_data:
        return False

    if user_id is not None:
        if int(
            session_data.get(
                "user_id",
                0,
            )
        ) != int(user_id):
            return False

    stored_version = int(
        session_data.get(
            "session_version",
            1,
        )
    )

    current_version = get_user_session_version(
        session_data.get(
            "user_id"
        )
    )

    if stored_version != current_version:
        delete_session(
            session_id
        )
        return False

    if enforce_idle:
        current_time = int(time.time())

        last_activity = int(
            session_data.get(
                "last_activity",
                0,
            )
        )

        if (
            current_time - last_activity
            >= settings.JWT_IDLE_TIMEOUT_SECONDS
        ):
            delete_session(
                session_id
            )

            return False

    return True


def update_session(
    session_id,
    user_id=None,
):
    session_data = get_session(
        session_id
    )

    if not session_data:
        return False

    if user_id is not None:
        if int(
            session_data.get(
                "user_id",
                0,
            )
        ) != int(user_id):
            return False

    stored_version = int(
        session_data.get(
            "session_version",
            1,
        )
    )

    current_version = get_user_session_version(
        session_data.get(
            "user_id"
        )
    )

    if stored_version != current_version:
        delete_session(
            session_id
        )

        return False

    current_time = int(time.time())

    last_activity = int(
        session_data.get(
            "last_activity",
            0,
        )
    )

    if (
        current_time - last_activity
        >= settings.JWT_IDLE_TIMEOUT_SECONDS
    ):
        delete_session(
            session_id
        )

        return False

    session_data["last_activity"] = (
        current_time
    )

    cache.set(
        session_key(session_id),
        json.dumps(session_data),
        timeout=settings.JWT_REFRESH_DAYS * 86400,
    )

    return True


def delete_session(session_id):
    session_data = get_session(
        session_id
    )

    cache.delete(
        session_key(session_id)
    )

    if session_data:
        user_id = session_data.get(
            "user_id"
        )

        if user_id:
            _remove_session_from_user_index(
                user_id,
                session_id,
            )


def get_user_sessions(user_id):
    session_ids = _get_user_session_ids(
        user_id
    )

    active_sessions = []
    valid_session_ids = []

    for session_id in session_ids:
        if not is_session_valid(
            session_id,
            user_id=user_id,
            enforce_idle=True,
        ):
            continue

        session_data = get_session(
            session_id
        )

        if not session_data:
            continue

        valid_session_ids.append(
            session_id
        )

        active_sessions.append(
            {
                "id": session_id,
                "user_id": int(
                    session_data.get(
                        "user_id",
                        user_id,
                    )
                ),
                "session_version": int(
                    session_data.get(
                        "session_version",
                        1,
                    )
                ),
                "created_at": session_data.get(
                    "created_at"
                ),
                "last_activity": session_data.get(
                    "last_activity"
                ),
                "ip_address": session_data.get(
                    "ip_address"
                ),
                "user_agent": session_data.get(
                    "user_agent",
                    "",
                ),
                "browser": session_data.get(
                    "browser",
                    "مرورگر",
                ),
                "os": session_data.get(
                    "os",
                    "نامشخص",
                ),
                "device_type": session_data.get(
                    "device_type",
                    "desktop",
                ),
                "device_name": session_data.get(
                    "device_name",
                    "مرورگر",
                ),
                "approximate_location": session_data.get(
                    "approximate_location"
                ),
            }
        )

    if valid_session_ids != session_ids:
        _save_user_session_ids(
            user_id,
            valid_session_ids,
        )

    active_sessions.sort(
        key=lambda item: (
            item.get("last_activity") or 0
        ),
        reverse=True,
    )

    return active_sessions


def delete_other_sessions(
    user_id,
    current_session_id,
):
    session_ids = _get_user_session_ids(
        user_id
    )

    deleted_count = 0

    for session_id in session_ids:
        if (
            str(session_id)
            == str(current_session_id)
        ):
            continue

        session_data = get_session(
            session_id
        )

        cache.delete(
            session_key(session_id)
        )

        if session_data:
            deleted_count += 1

    _save_user_session_ids(
        user_id,
        [
            str(current_session_id)
        ]
        if current_session_id
        else [],
    )

    return deleted_count


def ensure_session_registered(
    user_id,
    session_id,
    ip_address=None,
    user_agent="",
):
    if not session_id:
        return False

    session_data = get_session(
        session_id
    )

    if not session_data:
        return False

    if int(
        session_data.get(
            "user_id",
            0,
        )
    ) != int(user_id):
        return False

    changed = False

    if not session_data.get("created_at"):
        session_data["created_at"] = int(
            time.time()
        )
        changed = True

    if (
        not session_data.get("ip_address")
        and ip_address
    ):
        session_data["ip_address"] = ip_address
        changed = True

    if (
        not session_data.get("user_agent")
        and user_agent
    ):
        session_data["user_agent"] = str(
            user_agent
        )[:1000]
        changed = True

    if user_agent:
        parsed_user_agent = parse_user_agent(
            user_agent
        )

        if not session_data.get("browser"):
            session_data["browser"] = (
                parsed_user_agent["browser"]
            )
            changed = True

        if not session_data.get("os"):
            session_data["os"] = (
                parsed_user_agent["os"]
            )
            changed = True

        if not session_data.get("device_type"):
            session_data["device_type"] = (
                parsed_user_agent["device_type"]
            )
            changed = True

        if not session_data.get("device_name"):
            session_data["device_name"] = (
                parsed_user_agent["device_name"]
            )
            changed = True

    if "approximate_location" not in session_data:
        session_data["approximate_location"] = None
        changed = True

    if changed:
        cache.set(
            session_key(session_id),
            json.dumps(session_data),
            timeout=settings.JWT_REFRESH_DAYS * 86400,
        )

    _add_session_to_user_index(
        user_id,
        session_id,
    )

    return True