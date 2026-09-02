import hashlib
import secrets
from datetime import timedelta

import redis
from apps.accounts.models import OTPVerification
from django.conf import settings
from django.utils import timezone


def get_redis_client():
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


def generate_otp():
    return str(secrets.randbelow(1_000_000)).zfill(6)


def hash_otp(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def store_otp_code(challenge_id, code, ttl_seconds):
    client = get_redis_client()
    client.setex(f"otp:{challenge_id}", ttl_seconds, code)


def get_otp_code(challenge_id):
    return get_redis_client().get(f"otp:{challenge_id}")


def delete_otp_code(challenge_id):
    get_redis_client().delete(f"otp:{challenge_id}")


def is_expired(challenge):
    return challenge.expires_at <= timezone.now()


def invalidate_previous_challenges(phone_number, purpose):
    OTPVerification.objects.filter(
        phone_number=phone_number,
        purpose=purpose,
        is_used=False,
        expires_at__gt=timezone.now(),
    ).update(
        is_used=True,
        verified_at=timezone.now(),
    )


def can_resend(phone_number, purpose):
    last_request = (
        OTPVerification.objects
        .filter(
            phone_number=phone_number,
            purpose=purpose,
        )
        .order_by("-created_at")
        .first()
    )

    if not last_request:
        return True

    cooldown_until = (
            last_request.created_at
            + timedelta(
        seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
    )
    )

    return cooldown_until <= timezone.now()


def challenge_send_count(phone_number, purpose):
    window_start = (
            timezone.now()
            - timedelta(
        seconds=settings.OTP_SEND_WINDOW_SECONDS
    )
    )

    return (
        OTPVerification.objects
        .filter(
            phone_number=phone_number,
            purpose=purpose,
            created_at__gte=window_start,
        )
        .count()
    )


def check_and_increment_ip_rate_limit(ip_address, action):
    ip_address = ip_address or "unknown"

    client = get_redis_client()
    key = f"otp:ip-rate:{action}:{ip_address}"

    max_requests = settings.OTP_IP_MAX_REQUESTS
    window_seconds = settings.OTP_IP_WINDOW_SECONDS

    current_count = client.incr(key)

    print(
        f"IP RATE LIMIT | ACTION={action} | "
        f"IP={ip_address} | COUNT={current_count}"
    )

    if current_count == 1:
        client.expire(key, window_seconds)

    remaining = max(max_requests - current_count, 0)
    ttl = client.ttl(key)

    if ttl is None or ttl < 0:
        ttl = window_seconds

    return {
        "allowed": current_count <= max_requests,
        "count": current_count,
        "remaining": remaining,
        "retry_after": ttl,
    }


class OTPService:
    @staticmethod
    def generate_otp():
        return generate_otp()

    @staticmethod
    def hash_otp(code):
        return hash_otp(code)

    @staticmethod
    def get_otp_code(challenge_id):
        return get_otp_code(challenge_id)

    @staticmethod
    def delete_otp_code(challenge_id):
        delete_otp_code(challenge_id)

    @staticmethod
    def is_expired(challenge):
        return is_expired(challenge)

    @staticmethod
    def can_resend(phone_number, purpose):
        return can_resend(phone_number, purpose)

    @staticmethod
    def invalidate_previous_challenges(phone_number, purpose):
        invalidate_previous_challenges(phone_number, purpose)

    @staticmethod
    def challenge_send_count(phone_number, purpose):
        return challenge_send_count(phone_number, purpose)

    @staticmethod
    def check_and_increment_ip_rate_limit(ip_address, action):
        return check_and_increment_ip_rate_limit(
            ip_address,
            action,
        )
