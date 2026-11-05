from time import monotonic

from apps.pricing.providers.base import BasePriceProvider, PriceProviderError


class WallexProvider(BasePriceProvider):
    source = "wallex"
    base_url = "https://api.wallex.ir"

    def get_latest_price(self, symbol):
        symbol = self.validate_symbol(symbol)
        started_at = monotonic()

        data = self._get_json(
            "/v1/trades",
            params={"symbol": symbol},
        )

        if not isinstance(data, dict):
            raise PriceProviderError("Invalid Wallex response")

        if data.get("success") is False:
            raise PriceProviderError(
                f"Wallex API error: {data.get('message', 'unknown error')}"
            )

        result = data.get("result")
        if not isinstance(result, dict):
            raise PriceProviderError("Invalid Wallex result")

        trades = result.get("latestTrades")
        if not isinstance(trades, list) or not trades:
            raise PriceProviderError("Wallex returned no recent trades")

        valid_trades = []
        for trade in trades:
            if not isinstance(trade, dict):
                continue
            if str(trade.get("symbol", "")).upper() != symbol:
                continue

            try:
                price = self.parse_price(trade.get("price"))
                timestamp = self.parse_iso_timestamp(trade.get("timestamp"))
            except PriceProviderError:
                continue

            valid_trades.append((timestamp, price))

        if not valid_trades:
            raise PriceProviderError(
                "Wallex returned no valid trades for the requested symbol"
            )

        source_timestamp, price = max(valid_trades, key=lambda item: item[0])

        return self.build_price_data(
            symbol=symbol,
            price=price,
            source_timestamp=source_timestamp,
            started_at=started_at,
        )
