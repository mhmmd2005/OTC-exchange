from dataclasses import dataclass


class AddressValidationError(ValueError):
    pass


@dataclass(frozen=True)
class AddressValidationResult:
    normalized_address: str


class BaseAddressValidator:
    network_code = ""

    @classmethod
    def validate(cls, address):
        raise NotImplementedError