from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from apps.accounts.models import UserPreferences
from apps.notifications.models import Notification
from apps.notifications.email_templates import render_notification_email


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
    """Send a notification as HTML plus a plain-text fallback.

    Existing delivery rules are preserved:
    - The user's email must be present and verified.
    - Only security notifications may bypass the email preference.
    - Celery retries transient errors up to three times.
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

    # Never send account notifications to an unverified email address.
    if not user.email or not user.email_verified_at:
        return False

    # Only security notifications may bypass the user's email preference.
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

    # Plain-text fallback for clients that do not display HTML email.
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

    # Render a topic-specific HTML design from the central templates module.
    html_content = render_notification_email(
        notification=notification,
        user=user,
        frontend_url=frontend_url,
        force_email=force_email,
    )

    email = EmailMultiAlternatives(
        subject=notification.title,
        body="\n".join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")

    sent_count = email.send(fail_silently=False)

    if sent_count != 1:
        raise RuntimeError(
            "Notification email delivery failed for "
            f"notification_id={notification_id}"
        )

    return True
