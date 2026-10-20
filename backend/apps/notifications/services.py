import logging

from django.db import transaction

from apps.accounts.models import UserPreferences
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


def is_email_notification_enabled(user):
    """Return True only when the user's email is verified and enabled."""

    if not user.email or not user.email_verified_at:
        return False

    channels = (
        UserPreferences.objects
        .filter(user_id=user.pk)
        .values_list("notification_channels", flat=True)
        .first()
    )

    return (
        isinstance(channels, dict)
        and channels.get("email") is True
    )


def create_notification(
    *,
    user,
    category,
    title,
    message,
    action_label="",
    action_url="",
    send_email=False,
    force_email=False,
):
    """
    Create an in-app notification.

    Emails are opt-in per call: send_email=True is required for normal
    notifications. force_email=True bypasses the user's email preference
    only for security notifications, and still requires a verified email.
    """

    # Only password/security alerts may bypass the user's email preference.
    force_email = bool(
        force_email and category == "security"
    )

    try:
        with transaction.atomic():
            notification = Notification.objects.create(
                user=user,
                category=category,
                title=title,
                message=message,
                action_label=action_label,
                action_url=action_url,
            )

            should_send_email = (
                force_email
                or (
                    send_email
                    and is_email_notification_enabled(user)
                )
            )

            if should_send_email:
                from apps.notifications.tasks import (
                    send_notification_email_task,
                )

                notification_id = notification.pk

                transaction.on_commit(
                    lambda: send_notification_email_task.delay(
                        notification_id,
                        force_email,
                    ),
                    robust=True,
                )

        return notification

    except Exception:
        # Notification failures must not break financial operations.
        logger.exception(
            "Failed to create notification for user_id=%s",
            user.pk,
        )
        return None