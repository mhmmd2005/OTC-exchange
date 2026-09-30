from .base import AddressValidationError
from .bitcoin import BitcoinAddressValidator
from .ethereum import EthereumAddressValidator
from .tron import TronAddressValidator


VALIDATORS = {
    "BTC": BitcoinAddressValidator,
    "ERC20": EthereumAddressValidator,
    "TRC20": TronAddressValidator,
}


def get_validator(network_code):
    code = network_code.strip().upper()

    validator = VALIDATORS.get(code)

    if validator is None:
        raise AddressValidationError(
            f"برای شبکه {code} اعتبارسنجی آدرس هنوز پیاده‌سازی نشده است."
        )

    return validator