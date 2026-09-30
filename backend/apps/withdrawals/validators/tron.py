from .base import (
    AddressValidationError,
    AddressValidationResult,
    BaseAddressValidator,
)


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _sha256(data):
    import hashlib

    return hashlib.sha256(data).digest()


def _base58_decode(value):
    number = 0

    for char in value:
        if char not in BASE58_ALPHABET:
            raise AddressValidationError(
                "آدرس ترون معتبر نیست."
            )

        number = number * 58 + BASE58_ALPHABET.index(char)

    raw = number.to_bytes(
        max(
            1,
            (number.bit_length() + 7) // 8,
        ),
        "big",
    )

    leading_zeroes = len(
        value
    ) - len(
        value.lstrip("1")
    )

    return (
        b"\x00" * leading_zeroes
        + raw.lstrip(b"\x00")
    )


def _base58check_decode(value):
    decoded = _base58_decode(value)

    if len(decoded) < 5:
        raise AddressValidationError(
            "آدرس ترون معتبر نیست."
        )

    payload = decoded[:-4]
    checksum = decoded[-4:]

    expected = _sha256(
        _sha256(payload)
    )[:4]

    if checksum != expected:
        raise AddressValidationError(
            "checksum آدرس ترون معتبر نیست."
        )

    return payload


class TronAddressValidator(BaseAddressValidator):
    network_code = "TRC20"

    @classmethod
    def validate(cls, address):
        address = address.strip()

        if not address:
            raise AddressValidationError(
                "آدرس ترون را وارد کنید."
            )

        if len(address) != 34:
            raise AddressValidationError(
                "طول آدرس ترون معتبر نیست."
            )

        if not address.startswith("T"):
            raise AddressValidationError(
                "آدرس ترون باید با T شروع شود."
            )

        payload = _base58check_decode(
            address
        )

        if len(payload) != 21:
            raise AddressValidationError(
                "ساختار آدرس ترون معتبر نیست."
            )

        if payload[0] != 0x41:
            raise AddressValidationError(
                "این آدرس مربوط به شبکه اصلی ترون نیست."
            )

        return AddressValidationResult(
            normalized_address=address,
        )