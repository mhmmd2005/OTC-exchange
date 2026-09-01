import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseSMSProvider:
    def send_otp(self, phone_number, code):
        raise NotImplementedError


class ConsoleSMSProvider(BaseSMSProvider):
    def send_otp(self, phone_number, code):
        logger.warning("[DEV SMS] OTP sent to %s", phone_number)
        logger.warning("[DEV SMS] OTP code for %s: %s", phone_number, code)
        return True


class SMSService:
    def __init__(self, provider=None):
        provider_name = provider or settings.SMS_PROVIDER
        if provider_name == "console":
            self.provider = ConsoleSMSProvider()
        else:
            self.provider = ConsoleSMSProvider()

    def send_otp(self, phone_number, code):
        return self.provider.send_otp(phone_number, code)
