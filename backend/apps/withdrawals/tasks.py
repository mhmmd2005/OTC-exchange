from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.security.models import SecurityEvent
from apps.withdrawals.models import WithdrawalAddress


@shared_task
def activate_due_withdrawal_addresses():
    now = timezone.now()

    address_ids = list(
        WithdrawalAddress.objects.filter(
            status=WithdrawalAddress.Status.COOLING_DOWN,
            cooldown_until__isnull=False,
            cooldown_until__lte=now,
        )
        .order_by("id")
        .values_list("id", flat=True)[:100]
    )

    activated_count = 0

    for address_id in address_ids:
        with transaction.atomic():
            address = (
                WithdrawalAddress.objects
                .select_for_update()
                .select_related("user")
                .filter(id=address_id)
                .first()
            )

            if not address:
                continue

            if (
                address.status
                != WithdrawalAddress.Status.COOLING_DOWN
            ):
                continue

            if (
                not address.cooldown_until
                or address.cooldown_until > now
            ):
                continue

            address.status = WithdrawalAddress.Status.ACTIVE
            address.activated_at = now

            address.save(
                update_fields=[
                    "status",
                    "activated_at",
                    "updated_at",
                ]
            )

            SecurityEvent.objects.create(
                user=address.user,
                event_type="withdrawal_addr_activated",
                description=(
                    "Withdrawal address automatically activated "
                    "after cooldown."
                ),
                ip_address="system",
            )

            activated_count += 1

    return {
        "activated": activated_count,
    }