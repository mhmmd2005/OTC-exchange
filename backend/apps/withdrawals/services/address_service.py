import re

from apps.assets.models import AssetNetwork

from ..validators.base import (
    AddressValidationError,
    AddressValidationResult,
)
from ..validators.factory import get_validator


class WithdrawalAddressService:
    @staticmethod
    def validate(
        network: AssetNetwork,
        address: str,
    ) -> AddressValidationResult:
        address = address.strip()

        if not address:
            raise AddressValidationError(
                "آدرس برداشت را وارد کنید."
            )

        if network.status in {
            "disabled",
            "maintenance",
        }:
            raise AddressValidationError(
                "این شبکه در حال حاضر برای برداشت در دسترس نیست."
            )

        if not network.withdrawal_enabled:
            raise AddressValidationError(
                "برداشت روی این شبکه در حال حاضر فعال نیست."
            )

        if (
            network.asset
            and not network.asset.withdrawal_enabled
        ):
            raise AddressValidationError(
                "برداشت این ارز در حال حاضر فعال نیست."
            )

        if network.address_regex:
            try:
                pattern = re.compile(
                    network.address_regex
                )
            except re.error as exc:
                raise AddressValidationError(
                    "الگوی اعتبارسنجی این شبکه معتبر نیست."
                ) from exc

            if not pattern.fullmatch(address):
                raise AddressValidationError(
                    "آدرس با ساختار شبکه انتخاب‌شده سازگار نیست."
                )

        validator = get_validator(
            network.code
        )

        return validator.validate(
            address
        )