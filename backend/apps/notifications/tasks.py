from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from apps.accounts.models import UserPreferences
from apps.notifications.models import Notification


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": 3,
        "countdown": 30,
    },
    max_retries=3,
)
def send_notification_email_task(
    self,
    notification_id,
    force_email=False,
):
    """
    Send email for an explicitly email-enabled notification.

    A forced email bypasses the preference only for security alerts.
    A verified email address is always required.
    """

    notification = (
        Notification.objects
        .select_related("user")
        .filter(pk=notification_id)
        .first()
    )

    if notification is None:
        return False

    user = notification.user

    # Never send account notifications to an unverified address.
    if not user.email or not user.email_verified_at:
        return False

    # Prevent force-email from bypassing preferences for other categories.
    force_email = bool(
        force_email
        and notification.category == "security"
    )

    if not force_email:
        channels = (
            UserPreferences.objects
            .filter(user_id=user.pk)
            .values_list("notification_channels", flat=True)
            .first()
        )

        if (
            not isinstance(channels, dict)
            or channels.get("email") is not True
        ):
            return False

    frontend_url = getattr(
        settings,
        "FRONTEND_URL",
        "http://localhost:5173",
    ).rstrip("/")

    lines = [
        f"سلام {user.full_name or 'کاربر عزیز'}،",
        "",
        notification.message,
        "",
    ]

    if notification.action_url:
        action_url = notification.action_url.strip()

        if action_url.startswith(("https://", "http://")):
            full_action_url = action_url
        else:
            full_action_url = (
                f"{frontend_url}/{action_url.lstrip('/')}"
            )

        lines.extend([
            notification.action_label or "مشاهده جزئیات:",
            full_action_url,
            "",
        ])

    if force_email:
        lines.extend([
            "این پیام یک هشدار امنیتی حساب شماست.",
            "اگر این تغییر توسط شما انجام نشده است، "
            "حساب خود را بررسی کنید.",
            "",
        ])
    else:
        lines.extend([
            "این ایمیل طبق تنظیمات اعلان‌های حساب شما ارسال شده است.",
            "",
        ])

    lines.append("تیم روشا")

    sent_count = send_mail(
        subject=notification.title,
        message="\n".join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    if sent_count != 1:
        raise RuntimeError(
            "Notification email delivery failed for "
            f"notification_id={notification_id}"
        )

    return True