import re

from django.core.exceptions import ValidationError


def normalize_phone_number(phone_number):
    if phone_number is None:
        raise ValidationError("Phone number is required.")

    value = str(phone_number).strip()
    if not value:
        raise ValidationError("Phone number is required.")

    digits = re.sub(r"\D", "", value)

    if len(digits) == 11 and digits.startswith("0"):
        digits = "98" + digits[1:]
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "98" + digits
    elif len(digits) == 13 and digits.startswith("989"):
        digits = digits
    elif len(digits) == 12 and digits.startswith("98"):
        digits = digits

    if not re.fullmatch(r"989\d{9}", digits):
        raise ValidationError("Phone number must be a valid Iranian mobile number.")

    return f"+{digits}"
