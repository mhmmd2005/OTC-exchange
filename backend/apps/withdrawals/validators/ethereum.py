import re

from .base import (
    AddressValidationError,
    AddressValidationResult,
    BaseAddressValidator,
)


HEX_ADDRESS_RE = re.compile(
    r"^0x[0-9a-fA-F]{40}$"
)


def _keccak256(value):
    try:
        from Crypto.Hash import keccak
    except ImportError as exc:
        raise AddressValidationError(
            "ابزار بررسی checksum اتریوم روی سرور نصب نشده است."
        ) from exc

    digest = keccak.new(
        digest_bits=256
    )

    digest.update(
        value.encode("ascii")
    )

    return digest.hexdigest()


class EthereumAddressValidator(BaseAddressValidator):
    network_code = "ERC20"

    @classmethod
    def validate(cls, address):
        address = address.strip()

        if not HEX_ADDRESS_RE.fullmatch(address):
            raise AddressValidationError(
                "آدرس اتریوم باید با 0x شروع شود و ۴۰ رقم هگزادسیمال داشته باشد."
            )

        body = address[2:]

        if body.islower() or body.isupper():
            return AddressValidationResult(
                normalized_address=(
                    "0x" + body.lower()
                ),
            )

        expected_hash = _keccak256(
            body.lower()
        )

        for index, char in enumerate(body):
            if char.isdigit():
                continue

            if char.islower():
                expected_upper = (
                    int(expected_hash[index], 16)
                    >= 8
                )

                if expected_upper:
                    raise AddressValidationError(
                        "checksum آدرس اتریوم معتبر نیست."
                    )

            elif char.isupper():
                expected_upper = (
                    int(expected_hash[index], 16)
                    >= 8
                )

                if not expected_upper:
                    raise AddressValidationError(
                        "checksum آدرس اتریوم معتبر نیست."
                    )

        return AddressValidationResult(
            normalized_address=(
                "0x" + body.lower()
            ),
        )