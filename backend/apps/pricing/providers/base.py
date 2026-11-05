import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PriceProviderError(Exception):
    """Raised when an external price provider returns invalid data or fails."""


@dataclass(frozen=True, slots=True)
class PriceData:
    source: str
    symbol: str
    price: Decimal
    source_timestamp: datetime
    received_at: datetime
    latency_ms: int


class BasePriceProvider:
    source = ""
    base_url = ""
    timeout = 5
    max_response_size = 1_000_000

    def __init__(self, timeout=None):
        if timeout is not None:
            if timeout <= 0:
                raise ValueError("timeout must be greater than zero")
            self.timeout = timeout

    def _get_json(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        if params:
            url = f"{url}?{urlencode(params)}"

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "RoshaPricingEngine/1.0",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                if not 200 <= response.status < 300:
                    raise PriceProviderError(
                        f"{self.source}: unexpected HTTP status {response.status}"
                    )

                raw_data = response.read(self.max_response_size + 1)

            if len(raw_data) > self.max_response_size:
                raise PriceProviderError(
                    f"{self.source}: response exceeded the size limit"
                )

            return json.loads(raw_data.decode("utf-8"))

        except PriceProviderError:
            raise
        except HTTPError as exc:
            raise PriceProviderError(
                f"{self.source}: HTTP error {exc.code}"
            ) from exc
        except (URLError, TimeoutError, socket.timeout, OSError) as exc:
            raise PriceProviderError(
                f"{self.source}: connection failed"
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PriceProviderError(
                f"{self.source}: invalid JSON response"
            ) from exc

    @staticmethod
    def validate_symbol(symbol):
        symbol = str(symbol).strip().upper()
        if not symbol or not symbol.isalnum():
            raise PriceProviderError("Invalid market symbol")
        return symbol

    @staticmethod
    def parse_price(value):
        if value is None or isinstance(value, bool):
            raise PriceProviderError("Invalid price value")

        try:
            price = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise PriceProviderError("Invalid decimal price") from exc

        if not price.is_finite() or price <= 0:
            raise PriceProviderError("Price must be finite and positive")

        return price

    @staticmethod
    def parse_timestamp_ms(value):
        if value is None or isinstance(value, bool):
            raise PriceProviderError("Invalid timestamp")

        try:
            timestamp_ms = Decimal(str(value))
            if (
                not timestamp_ms.is_finite()
                or timestamp_ms <= 0
                or timestamp_ms != timestamp_ms.to_integral_value()
            ):
                raise ValueError("Timestamp must be a positive integer")

            return datetime.fromtimestamp(
                float(timestamp_ms / Decimal("1000")),
                tz=timezone.utc,
            )
        except (InvalidOperation, ValueError, TypeError, OverflowError, OSError) as exc:
            raise PriceProviderError("Invalid millisecond timestamp") from exc

    @staticmethod
    def parse_iso_timestamp(value):
        if not isinstance(value, str) or not value.strip():
            raise PriceProviderError("Invalid ISO timestamp")

        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("Timestamp must include a timezone")
            return timestamp.astimezone(timezone.utc)
        except (ValueError, OverflowError) as exc:
            raise PriceProviderError("Invalid ISO timestamp") from exc

    def build_price_data(self, symbol, price, source_timestamp, started_at):
        return PriceData(
            source=self.source,
            symbol=symbol,
            price=price,
            source_timestamp=source_timestamp,
            received_at=datetime.now(timezone.utc),
            latency_ms=max(0, int((monotonic() - started_at) * 1000)),
        )
