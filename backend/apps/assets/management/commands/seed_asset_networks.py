from django.core.management.base import BaseCommand, CommandError

from apps.assets.models import Asset, AssetNetwork


NETWORKS = [
    {
        "asset": "BTC",
        "code": "BTC",
        "name": "Bitcoin",
        "display_name": "بیت‌کوین",
        "address_regex": "",
        "memo_required": False,
        "deposit_enabled": True,
        "withdrawal_enabled": True,
        "status": "active",
        "confirmations": 3,
        "estimated_arrival_minutes": 30,
        "minimum_deposit": "0.0001",
        "minimum_withdrawal": "0.0005",
        "withdrawal_fee": "0.00018",
    },
    {
        "asset": "USDT",
        "code": "TRC20",
        "name": "Tron",
        "display_name": "ترون (TRC20)",
        "address_regex": r"^T[1-9A-HJ-NP-Za-km-z]{33}$",
        "memo_required": False,
        "deposit_enabled": True,
        "withdrawal_enabled": True,
        "status": "active",
        "confirmations": 20,
        "estimated_arrival_minutes": 3,
        "minimum_deposit": "1",
        "minimum_withdrawal": "10",
        "withdrawal_fee": "1",
    },
    {
        "asset": "USDT",
        "code": "ERC20",
        "name": "Ethereum",
        "display_name": "اتریوم (ERC20)",
        "address_regex": r"^0x[a-fA-F0-9]{40}$",
        "memo_required": False,
        "deposit_enabled": True,
        "withdrawal_enabled": True,
        "status": "congested",
        "confirmations": 12,
        "estimated_arrival_minutes": 15,
        "minimum_deposit": "5",
        "minimum_withdrawal": "20",
        "withdrawal_fee": "6.5",
    },
]


class Command(BaseCommand):
    help = "Create or update supported asset networks."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for item in NETWORKS:
            asset_symbol = item["asset"]

            try:
                asset = Asset.objects.get(
                    symbol=asset_symbol.upper(),
                    is_active=True,
                )
            except Asset.DoesNotExist as exc:
                raise CommandError(
                    f"Asset '{asset_symbol}' does not exist or is inactive."
                ) from exc

            defaults = {
                "name": item["name"],
                "display_name": item["display_name"],
                "address_regex": item["address_regex"],
                "memo_required": item["memo_required"],
                "deposit_enabled": item["deposit_enabled"],
                "withdrawal_enabled": item["withdrawal_enabled"],
                "status": item["status"],
                "confirmations": item["confirmations"],
                "estimated_arrival_minutes": item["estimated_arrival_minutes"],
                "minimum_deposit": item["minimum_deposit"],
                "minimum_withdrawal": item["minimum_withdrawal"],
                "withdrawal_fee": item["withdrawal_fee"],
            }

            _, created = AssetNetwork.objects.update_or_create(
                asset=asset,
                code=item["code"].upper(),
                defaults=defaults,
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created: {asset.symbol} / {item['code']}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Updated: {asset.symbol} / {item['code']}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created={created_count}, Updated={updated_count}"
            )
        )