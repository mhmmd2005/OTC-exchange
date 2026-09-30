from .base import (
    AddressValidationError,
    AddressValidationResult,
    BaseAddressValidator,
)


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

BECH32_CONST = 1
BECH32M_CONST = 0x2BC830A3


def _sha256(data):
    import hashlib

    return hashlib.sha256(data).digest()


def _base58_decode(value):
    number = 0

    for char in value:
        if char not in BASE58_ALPHABET:
            raise AddressValidationError(
                "آدرس بیت‌کوین معتبر نیست."
            )

        number = number * 58 + BASE58_ALPHABET.index(char)

    raw = number.to_bytes(
        max(1, (number.bit_length() + 7) // 8),
        "big",
    )

    leading_zeroes = len(value) - len(value.lstrip("1"))

    return b"\x00" * leading_zeroes + raw.lstrip(b"\x00")


def _base58check_decode(value):
    decoded = _base58_decode(value)

    if len(decoded) < 5:
        raise AddressValidationError(
            "آدرس بیت‌کوین معتبر نیست."
        )

    payload = decoded[:-4]
    checksum = decoded[-4:]

    expected = _sha256(
        _sha256(payload)
    )[:4]

    if checksum != expected:
        raise AddressValidationError(
            "checksum آدرس بیت‌کوین معتبر نیست."
        )

    return payload


def _bech32_polymod(values):
    generator = [
        0x3B6A57B2,
        0x26508E6D,
        0x1EA119FA,
        0x3D4233DD,
        0x2A1462B3,
    ]

    checksum = 1

    for value in values:
        top = checksum >> 25

        checksum = (
            (checksum & 0x1FFFFFF) << 5
        ) ^ value

        for index in range(5):
            if (top >> index) & 1:
                checksum ^= generator[index]

    return checksum


def _bech32_hrp_expand(hrp):
    return (
        [ord(char) >> 5 for char in hrp]
        + [0]
        + [ord(char) & 31 for char in hrp]
    )


def _bech32_verify_checksum(hrp, data):
    polymod = _bech32_polymod(
        _bech32_hrp_expand(hrp) + data
    )

    if polymod == BECH32_CONST:
        return "bech32"

    if polymod == BECH32M_CONST:
        return "bech32m"

    raise AddressValidationError(
        "checksum آدرس بیت‌کوین معتبر نیست."
    )


def _bech32_decode(value):
    if not value:
        raise AddressValidationError(
            "آدرس بیت‌کوین معتبر نیست."
        )

    if value.lower() != value and value.upper() != value:
        raise AddressValidationError(
            "حروف بزرگ و کوچک آدرس بیت‌کوین معتبر نیستند."
        )

    value = value.lower()

    separator = value.rfind("1")

    if separator < 1 or separator + 7 > len(value):
        raise AddressValidationError(
            "ساختار آدرس بیت‌کوین معتبر نیست."
        )

    hrp = value[:separator]
    data_part = value[separator + 1:]

    data = []

    for char in data_part:
        if char not in BECH32_CHARSET:
            raise AddressValidationError(
                "آدرس بیت‌کوین معتبر نیست."
            )

        data.append(
            BECH32_CHARSET.index(char)
        )

    encoding = _bech32_verify_checksum(
        hrp,
        data,
    )

    return hrp, data[:-6], encoding


def _convertbits(data, from_bits, to_bits, pad):
    accumulator = 0
    bits = 0
    result = []
    max_value = (1 << to_bits) - 1
    max_accumulator = (1 << (from_bits + to_bits - 1)) - 1

    for value in data:
        if value < 0 or value >> from_bits:
            raise AddressValidationError(
                "داده آدرس بیت‌کوین معتبر نیست."
            )

        accumulator = (
            (accumulator << from_bits) | value
        ) & max_accumulator

        bits += from_bits

        while bits >= to_bits:
            bits -= to_bits
            result.append(
                (accumulator >> bits) & max_value
            )

    if pad:
        if bits:
            result.append(
                (accumulator << (to_bits - bits))
                & max_value
            )
    else:
        if bits >= from_bits:
            raise AddressValidationError(
                "داده آدرس بیت‌کوین معتبر نیست."
            )

        if (
            (accumulator << (to_bits - bits))
            & max_value
        ):
            raise AddressValidationError(
                "padding آدرس بیت‌کوین معتبر نیست."
            )

    return result


class BitcoinAddressValidator(BaseAddressValidator):
    network_code = "BTC"

    @classmethod
    def validate(cls, address):
        address = address.strip()

        if not address:
            raise AddressValidationError(
                "آدرس بیت‌کوین را وارد کنید."
            )

        if len(address) < 14 or len(address) > 90:
            raise AddressValidationError(
                "طول آدرس بیت‌کوین معتبر نیست."
            )

        if address.lower().startswith("bc1"):
            return cls._validate_segwit(address)

        return cls._validate_base58(address)

    @classmethod
    def _validate_base58(cls, address):
        payload = _base58check_decode(address)

        if len(payload) != 21:
            raise AddressValidationError(
                "ساختار آدرس بیت‌کوین معتبر نیست."
            )

        version = payload[0]

        if version not in {0x00, 0x05}:
            raise AddressValidationError(
                "این آدرس مربوط به شبکه اصلی بیت‌کوین نیست."
            )

        return AddressValidationResult(
            normalized_address=address,
        )

    @classmethod
    def _validate_segwit(cls, address):
        hrp, data, encoding = _bech32_decode(address)

        if hrp != "bc":
            raise AddressValidationError(
                "آدرس مربوط به شبکه اصلی بیت‌کوین نیست."
            )

        if not data:
            raise AddressValidationError(
                "آدرس بیت‌کوین معتبر نیست."
            )

        witness_version = data[0]

        if witness_version > 16:
            raise AddressValidationError(
                "نسخه witness آدرس بیت‌کوین معتبر نیست."
            )

        if witness_version == 0 and encoding != "bech32":
            raise AddressValidationError(
                "checksum آدرس witness معتبر نیست."
            )

        if witness_version != 0 and encoding != "bech32m":
            raise AddressValidationError(
                "checksum آدرس witness معتبر نیست."
            )

        witness_program = _convertbits(
            data[1:],
            5,
            8,
            False,
        )

        if not 2 <= len(witness_program) <= 40:
            raise AddressValidationError(
                "طول witness program معتبر نیست."
            )

        if witness_version == 0 and len(witness_program) not in {
            20,
            32,
        }:
            raise AddressValidationError(
                "آدرس witness نسخه صفر معتبر نیست."
            )

        return AddressValidationResult(
            normalized_address=address.lower(),
        )