import json
from urllib import request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import BankCardPrefix, IranianBank
from apps.accounts.services.bank_registry import normalize_digits


class Command(BaseCommand):
    help = "Synchronize trusted Iranian bank registry data."

    def add_arguments(self, parser):
        parser.add_argument("--source-url", default="", dest="source_url")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        source_url = (options["source_url"] or getattr(settings, "BANK_REGISTRY_SOURCE_URL", "")).strip()
        dry_run = options["dry_run"]

        if not source_url:
            raise CommandError(
                "Bank registry source is not configured. Set BANK_REGISTRY_SOURCE_URL or pass --source-url."
            )

        self.stdout.write(f"Starting bank registry sync from {source_url}...")
        registry = self._fetch_registry(source_url)
        if registry is None:
            raise CommandError("Bank registry source did not return a usable payload.")

        banks = self._build_registry(registry)
        if not banks:
            raise CommandError("Bank registry source is empty or structurally invalid.")

        current_prefixes = set()
        for bank_info in banks.values():
            current_prefixes.update(bank_info["prefixes"])

        if dry_run:
            counts = self._calculate_dry_run_changes(source_url, banks)
            self.stdout.write(
                self.style.WARNING(
                    "Dry run only. Would create={created}, update={updated}, deactivate={deactivated}.".format(
                        **counts
                    )
                )
            )
            return

        with transaction.atomic():
            created = 0
            updated = 0
            deactivated = 0

            for info in banks.values():
                bank, created_flag = IranianBank.objects.get_or_create(
                    name_en=info["name_en"],
                    defaults={
                        "name_fa": info["name_fa"],
                        "sheba_code": info["sheba_code"],
                        "is_active": True,
                        "color": info["color"],
                        "logo_url": info["logo_url"],
                        "card_prefixes": sorted(info["prefixes"]),
                    },
                )

                if created_flag:
                    created += 1
                elif (
                    bank.name_fa != info["name_fa"]
                    or bank.sheba_code != info["sheba_code"]
                    or bank.card_prefixes != sorted(info["prefixes"])
                ):
                    bank.name_fa = info["name_fa"]
                    bank.sheba_code = info["sheba_code"]
                    bank.is_active = True
                    bank.color = info["color"]
                    bank.logo_url = info["logo_url"]
                    bank.card_prefixes = sorted(info["prefixes"])
                    bank.save(update_fields=["name_fa", "sheba_code", "is_active", "color", "logo_url", "card_prefixes"])
                    updated += 1

                for prefix in info["prefixes"]:
                    obj, prefix_created = BankCardPrefix.objects.get_or_create(
                        bank=bank,
                        prefix=prefix,
                        defaults={
                            "is_active": True,
                            "is_legacy": False,
                            "source": "trusted_registry",
                            "source_url": source_url,
                            "verified_at": timezone.now(),
                        },
                    )
                    if prefix_created:
                        created += 1
                    elif (
                        obj.is_active is not True
                        or obj.is_legacy
                        or obj.source != "trusted_registry"
                        or obj.source_url != source_url
                    ):
                        obj.is_active = True
                        obj.is_legacy = False
                        obj.source = "trusted_registry"
                        obj.source_url = source_url
                        obj.verified_at = timezone.now()
                        obj.save(update_fields=["is_active", "is_legacy", "source", "source_url", "verified_at"])
                        updated += 1

            stale_prefixes = BankCardPrefix.objects.filter(source_url=source_url).exclude(prefix__in=current_prefixes)
            if stale_prefixes.exists():
                deactivated = stale_prefixes.count()
                stale_prefixes.update(is_active=False, is_legacy=True)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Bank registry sync complete. Created={created}, updated={updated}, deactivated={deactivated}."
                )
            )

    def _calculate_dry_run_changes(self, source_url, banks):
        created = 0
        updated = 0
        deactivated = 0
        current_prefixes = set()
        for info in banks.values():
            current_prefixes.update(info["prefixes"])

        for info in banks.values():
            bank, created_flag = IranianBank.objects.get_or_create(
                name_en=info["name_en"],
                defaults={
                    "name_fa": info["name_fa"],
                    "sheba_code": info["sheba_code"],
                    "is_active": True,
                    "color": info["color"],
                    "logo_url": info["logo_url"],
                    "card_prefixes": sorted(info["prefixes"]),
                },
            )
            if created_flag:
                created += 1
            elif (
                bank.name_fa != info["name_fa"]
                or bank.sheba_code != info["sheba_code"]
                or bank.card_prefixes != sorted(info["prefixes"])
            ):
                updated += 1

            for prefix in info["prefixes"]:
                obj = BankCardPrefix.objects.filter(bank=bank, prefix=prefix).first()
                if obj is None:
                    created += 1
                elif (
                    obj.is_active is not True
                    or obj.is_legacy
                    or obj.source != "trusted_registry"
                    or obj.source_url != source_url
                ):
                    updated += 1

        stale_prefixes = BankCardPrefix.objects.filter(source_url=source_url).exclude(prefix__in=current_prefixes)
        if stale_prefixes.exists():
            deactivated = stale_prefixes.count()

        return {"created": created, "updated": updated, "deactivated": deactivated}

    def _fetch_registry(self, source_url):
        try:
            with request.urlopen(source_url, timeout=20) as response:
                payload = response.read().decode("utf-8")
        except Exception as exc:
            raise CommandError(f"Unable to fetch registry source: {exc}")

        try:
            registry = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Registry source did not return valid JSON: {exc}")

        if registry in ({}, [], None):
            raise CommandError("Registry source is empty.")

        return registry

    def _build_registry(self, registry):
        data = registry.get("banks") if isinstance(registry, dict) else None
        if data is None and isinstance(registry, dict):
            data = registry.get("data") or registry
        if isinstance(data, dict):
            data = [data]
        if data is None:
            data = []

        banks = {}
        for record in data or []:
            if not isinstance(record, dict):
                continue
            name_fa = str(record.get("name_fa") or record.get("nameFa") or record.get("name") or "").strip()
            name_en = str(record.get("name_en") or record.get("nameEn") or record.get("englishName") or name_fa or "Unknown Bank").strip()
            sheba_code = str(record.get("sheba_code") or record.get("shebaCode") or "").strip()[:3]
            prefixes = record.get("card_prefixes") or record.get("cardPrefixes") or record.get("prefixes") or []
            if not isinstance(prefixes, list):
                prefixes = [str(prefixes)] if prefixes else []
            cleaned_prefixes = set()
            for prefix in prefixes:
                cleaned = normalize_digits(str(prefix)).strip()
                if not cleaned or not cleaned.isdigit():
                    continue
                cleaned = cleaned[:16]
                if len(cleaned) >= 6:
                    cleaned_prefixes.add(cleaned)

            if not name_fa and not name_en:
                continue
            if not cleaned_prefixes:
                continue

            bank_key = sheba_code or name_en.lower()
            banks[bank_key] = {
                "name_fa": name_fa or name_en,
                "name_en": name_en or name_fa,
                "sheba_code": sheba_code,
                "color": record.get("color") or "#6366f1",
                "logo_url": record.get("logo_url") or record.get("logoUrl") or "",
                "prefixes": sorted(cleaned_prefixes),
            }

        return banks
