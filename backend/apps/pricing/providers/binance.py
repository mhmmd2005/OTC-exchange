from time import monotonic

from apps.pricing.providers.base import BasePriceProvider, PriceProviderError


class BinanceProvider(BasePriceProvider):
    source = "binance"
    base_url = "https://data-api.binance.vision"

    def get_latest_price(self, symbol):
        symbol = self.validate_symbol(symbol)
        started_at = monotonic()

        data = self._get_json(
            "/api/v3/trades",
            params={"symbol": symbol, "limit": 1},
        )

        if not isinstance(data, list) or not data:
            raise PriceProviderError("Binance returned no recent trades")

        valid_trades = []
        for trade in data:
            if not isinstance(trade, dict):
                continue
            try:
                price = self.parse_price(trade.get("price"))
                timestamp = self.parse_timestamp_ms(trade.get("time"))
            except PriceProviderError:
                continue
            valid_trades.append((timestamp, price))

        if not valid_trades:
            raise PriceProviderError("Binance returned no valid trades")

        # Select by source timestamp rather than assuming response ordering.
        source_timestamp, price = max(valid_trades, key=lambda item: item[0])

        return self.build_price_data(
            symbol=symbol,
            price=price,
            source_timestamp=source_timestamp,
            started_at=started_at,
        )
