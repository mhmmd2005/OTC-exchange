import time

from apps.accounts.services.session import (
    delete_session,
    get_session,
    get_user_session_version,
)
from django.conf import settings
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication


class IdleTimeoutJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)

        if result is None:
            return None

        user, token = result
        session_id = token.get("session_id")

        if not session_id:
            raise exceptions.AuthenticationFailed(
                "Session ID is required."
            )

        session = get_session(session_id)

        if not session:
            raise exceptions.AuthenticationFailed(
                "Session not found or expired."
            )

        if int(session.get("user_id", 0)) != int(user.id):
            delete_session(session_id)
            raise exceptions.AuthenticationFailed(
                "Session user mismatch."
            )

        session_version = int(
            session.get("session_version", 1)
        )

        current_version = get_user_session_version(
            user.id
        )

        if session_version != current_version:
            delete_session(session_id)
            raise exceptions.AuthenticationFailed(
                "Session has been revoked."
            )

        current_time = int(time.time())
        last_activity = int(
            session.get("last_activity", 0)
        )

        if (
                current_time - last_activity
                >= settings.JWT_IDLE_TIMEOUT_SECONDS
        ):
            delete_session(session_id)
            raise exceptions.AuthenticationFailed(
                "Session has expired due to inactivity."
            )

        return user, token
