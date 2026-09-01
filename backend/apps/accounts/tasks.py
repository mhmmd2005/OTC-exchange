from celery import shared_task
from django.utils import timezone

from apps.accounts.models import OTPVerification
from apps.accounts.services.otp import get_otp_code
from apps.accounts.services.sms import SMSService


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 30}, max_retries=3)
def send_otp_sms_task(self, challenge_id):
    challenge = OTPVerification.objects.filter(id=challenge_id).first()
    if not challenge:
        return False
    if challenge.is_used or challenge.expires_at <= timezone.now():
        return False

    code = get_otp_code(challenge.id)
    if not code:
        return False

    result = SMSService().send_otp(challenge.phone_number, code)
    if result:
        challenge.delivery_status = "sent"
        challenge.last_sent_at = timezone.now()
        challenge.save(update_fields=["delivery_status", "last_sent_at"])
        return True

    challenge.delivery_status = "failed"
    challenge.save(update_fields=["delivery_status"])
    return False
