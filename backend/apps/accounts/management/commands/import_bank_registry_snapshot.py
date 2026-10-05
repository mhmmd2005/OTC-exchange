import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import BankCardPrefix, IranianBank
from apps.accounts.services.bank_registry import normalize_digits

DEFAULT_SNAPSHOT = (
    Path(settings.BASE_DIR)
    / "apps"
    / "accounts"
    / "registry"
    / "iran_banks_registry_2026_10.json"
)

SOURCE_NAME = "curated_snapshot_2026_10"
SOURCE_URL = ""


class Command(BaseCommand):
    help = "Import a reviewed Iranian bank card-prefix registry snapshot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(DEFAULT_SNAPSHOT),
            help="Path to the registry JSON snapshot.",
        )

    def handle(self, *args, **options):
        snapshot_path = Path(options["path"]).expanduser().resolve()

        if not snapshot_path.is_file():
            raise CommandError(
                f"Registry snapshot not found: {snapshot_path}"
            )

        try:
            payload = json.loads(
                snapshot_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise CommandError(
                f"Registry snapshot contains invalid JSON: {exc}"
            ) from exc

        banks = payload.get("banks")
        if not isinstance(banks, list) or not banks:
            raise CommandError(
                "Registry snapshot does not contain a usable 'banks' list."
            )

        normalized_banks = self._normalize_snapshot(banks)
        self._validate_snapshot(normalized_banks)
        self._validate_database_conflicts(normalized_banks)

        created_banks = 0
        updated_banks = 0
        created_prefixes = 0
        updated_prefixes = 0

        verified_at = timezone.now()

        with transaction.atomic():
            for bank_info in normalized_banks:
                bank, created = IranianBank.objects.get_or_create(
                    name_en=bank_info["name_en"],
                    defaults={
                        "name_fa": bank_info["name_fa"],
                        "sheba_code": bank_info["sheba_code"],
                        "is_active": True,
                    },
                )

                if created:
                    created_banks += 1
                else:
                    changed = False

                    if bank.name_fa != bank_info["name_fa"]:
                        bank.name_fa = bank_info["name_fa"]
                        changed = True

                    if bank.sheba_code != bank_info["sheba_code"]:
                        bank.sheba_code = bank_info["sheba_code"]
                        changed = True

                    if not bank.is_active:
                        bank.is_active = True
                        changed = True

                    if changed:
                        bank.save(
                            update_fields=[
                                "name_fa",
                                "sheba_code",
                                "is_active",
                            ]
                        )
                        updated_banks += 1

                for prefix, is_legacy in bank_info["prefixes"]:
                    prefix_obj, created = BankCardPrefix.objects.get_or_create(
                        prefix=prefix,
                        defaults={
                            "bank": bank,
                            "is_active": True,
                            "is_legacy": is_legacy,
                            "source": SOURCE_NAME,
                            "source_url": SOURCE_URL,
                            "verified_at": verified_at,
                        },
                    )

                    if created:
                        created_prefixes += 1
                        continue

                    changed_fields = []

                    if prefix_obj.bank_id != bank.id:
                        raise CommandError(
                            f"Prefix {prefix} already belongs to another bank."
                        )

                    if not prefix_obj.is_active:
                        prefix_obj.is_active = True
                        changed_fields.append("is_active")

                    if prefix_obj.is_legacy != is_legacy:
                        prefix_obj.is_legacy = is_legacy
                        changed_fields.append("is_legacy")

                    if prefix_obj.source != SOURCE_NAME:
                        prefix_obj.source = SOURCE_NAME
                        changed_fields.append("source")

                    if prefix_obj.source_url != SOURCE_URL:
                        prefix_obj.source_url = SOURCE_URL
                        changed_fields.append("source_url")

                    prefix_obj.verified_at = verified_at
                    changed_fields.append("verified_at")

                    if changed_fields:
                        prefix_obj.save(
                            update_fields=changed_fields
                                          + ["updated_at"]
                        )
                        updated_prefixes += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Bank registry snapshot imported successfully. "
                f"Banks created={created_banks}, "
                f"banks updated={updated_banks}, "
                f"prefixes created={created_prefixes}, "
                f"prefixes updated={updated_prefixes}."
            )
        )

    def _normalize_snapshot(self, banks):
        result = []

        for record in banks:
            if not isinstance(record, dict):
                raise CommandError(
                    "Every bank record must be a JSON object."
                )

            name_fa = str(
                record.get("name_fa") or ""
            ).strip()
            name_en = str(
                record.get("name_en") or ""
            ).strip()
            sheba_code = normalize_digits(
                str(record.get("sheba_code") or "")
            ).strip()

            if not name_fa or not name_en:
                raise CommandError(
                    "Every bank must have name_fa and name_en."
                )

            if sheba_code and (
                    len(sheba_code) != 3
                    or not sheba_code.isdigit()
            ):
                raise CommandError(
                    f"Invalid sheba_code for {name_en}: {sheba_code!r}"
                )

            prefixes = []

            for raw_prefix in record.get("prefixes", []):
                prefix = normalize_digits(
                    str(raw_prefix)
                ).strip()

                if not prefix.isdigit() or len(prefix) < 6:
                    raise CommandError(
                        f"Invalid card prefix for {name_en}: "
                        f"{raw_prefix!r}"
                    )

                prefixes.append((prefix[:16], False))

            for raw_prefix in record.get("legacy_prefixes", []):
                prefix = normalize_digits(
                    str(raw_prefix)
                ).strip()

                if not prefix.isdigit() or len(prefix) < 6:
                    raise CommandError(
                        f"Invalid legacy card prefix for {name_en}: "
                        f"{raw_prefix!r}"
                    )

                prefixes.append((prefix[:16], True))

            result.append(
                {
                    "name_fa": name_fa,
                    "name_en": name_en,
                    "sheba_code": sheba_code,
                    "prefixes": prefixes,
                }
            )

        return result

    def _validate_snapshot(self, banks):
        seen = {}

        for bank in banks:
            for prefix, is_legacy in bank["prefixes"]:
                previous = seen.get(prefix)

                if previous is not None:
                    previous_bank, previous_legacy = previous
                    raise CommandError(
                        "Conflicting snapshot data: "
                        f"prefix {prefix} appears for both "
                        f"{previous_bank} and {bank['name_en']}."
                    )

                seen[prefix] = (
                    bank["name_en"],
                    is_legacy,
                )

    def _validate_database_conflicts(self, banks):
        incoming = {}

        for bank in banks:
            for prefix, is_legacy in bank["prefixes"]:
                incoming[prefix] = bank["name_en"]

        existing = (
            BankCardPrefix.objects
            .filter(prefix__in=incoming.keys())
            .select_related("bank")
        )

        for prefix_obj in existing:
            expected_bank = incoming[prefix_obj.prefix]

            if prefix_obj.bank.name_en != expected_bank:
                raise CommandError(
                    "Database conflict: "
                    f"prefix {prefix_obj.prefix} already belongs to "
                    f"{prefix_obj.bank.name_en}, but snapshot assigns it to "
                    f"{expected_bank}."
                )
