import hashlib
import hmac
import re

from django.conf import settings

from apps.accounts.models import BankCardPrefix, BankVerificationObservation, IranianBank


class BankRegistryError(Exception):
    pass


def normalize_digits(value):
    return str(value).translate(
        str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789",
        )
    )


def normalize_card(value):
    return re.sub(r"\D", "", normalize_digits(value))


def normalize_iban(value):
    return normalize_digits(value).replace(" ", "").replace("-", "").upper()


def is_valid_card_number(value):
    digits = normalize_card(value)
    if len(digits) != 16 or not digits.isdigit() or len(set(digits)) == 1:
        return False

    total = 0
    digits_reversed = reversed(digits)
    for index, char in enumerate(digits_reversed):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit

    return total % 10 == 0


def is_valid_iranian_iban(value):
    iban = normalize_iban(value)
    if not re.fullmatch(r"IR\d{24}", iban):
        return False

    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(ord(ch.upper()) - 55) if ch.isalpha() else ch for ch in rearranged)
    remainder = 0
    for char in numeric:
        remainder = (remainder * 10 + int(char)) % 97
    return remainder == 1


def get_iban_bank_code(value):
    iban = normalize_iban(value)
    if not re.fullmatch(r"IR\d{24}", iban):
        return None
    return iban[4:7]


def find_bank_by_card(card_number):
    digits = normalize_card(card_number)
    if len(digits) < 6:
        return None

    best_bank = None
    best_prefix_length = 0

    prefixes = BankCardPrefix.objects.filter(is_active=True, prefix__isnull=False).select_related("bank").order_by("-prefix")
    for prefix_obj in prefixes:
        prefix = normalize_digits(prefix_obj.prefix).strip()
        if prefix.isdigit() and len(prefix) >= 6 and digits.startswith(prefix) and len(prefix) > best_prefix_length:
            best_bank = prefix_obj.bank
            best_prefix_length = len(prefix)

    if best_bank is not None:
        return best_bank

    banks = IranianBank.objects.filter(is_active=True).prefetch_related("bank_card_prefixes")
    for bank in banks:
        for prefix_obj in bank.bank_card_prefixes.filter(is_active=True):
            prefix = normalize_digits(prefix_obj.prefix).strip()
            if prefix.isdigit() and len(prefix) >= 6 and digits.startswith(prefix) and len(prefix) > best_prefix_length:
                best_bank = bank
                best_prefix_length = len(prefix)

        for raw_prefix in bank.card_prefixes or []:
            prefix = normalize_digits(raw_prefix).strip()
            if prefix.isdigit() and len(prefix) >= 6 and digits.startswith(prefix) and len(prefix) > best_prefix_length:
                best_bank = bank
                best_prefix_length = len(prefix)

    return best_bank


def find_bank_by_iban(iban):
    bank_code = get_iban_bank_code(iban)
    if not bank_code:
        return None
    return IranianBank.objects.filter(is_active=True, sheba_code=bank_code).first()


def resolve_bank_identity(card_number, iban):
    return find_bank_by_card(card_number), find_bank_by_iban(iban)


def create_bank_verification_observation(
    *,
    user=None,
    card_number="",
    iban="",
    card_luhn_valid=False,
    iban_checksum_valid=False,
    card_bank_known=False,
    iban_bank_known=False,
    banks_match=False,
    card_ownership_verified=False,
    iban_ownership_verified=False,
    result="invalid_card",
    failure_reason="",
    observed_card_prefix="",
):
    normalized_card = normalize_card(card_number)
    normalized_iban = normalize_iban(iban)
    prefix = normalized_card[:6] if len(normalized_card) >= 6 else ""
    observed_prefix = normalize_card(observed_card_prefix)[:10] if observed_card_prefix else prefix
    last4 = normalized_card[-4:] if len(normalized_card) >= 4 else ""
    secret = settings.SECRET_KEY.encode("utf-8")

    def fingerprint(value):
        if not value:
            return ""
        return hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()

    return BankVerificationObservation.objects.create(
        user=user,
        card_prefix=prefix,
        observed_card_prefix=observed_prefix,
        card_last4=last4,
        card_fingerprint=fingerprint(normalized_card),
        iban_bank_code=get_iban_bank_code(normalized_iban) or "",
        iban_fingerprint=fingerprint(normalized_iban),
        card_luhn_valid=bool(card_luhn_valid),
        iban_checksum_valid=bool(iban_checksum_valid),
        card_bank_known=bool(card_bank_known),
        iban_bank_known=bool(iban_bank_known),
        banks_match=bool(banks_match),
        card_ownership_verified=bool(card_ownership_verified),
        iban_ownership_verified=bool(iban_ownership_verified),
        result=result,
        failure_reason=failure_reason,
    )