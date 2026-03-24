"""Pydantic models for MEXC market data API responses.

Covers:
- Ticker  — 24-hour rolling window price change statistics
- OrderBook   — bids/asks as (price, quantity) Decimal pairs
- Kline       — OHLCV candlestick data
- Trade       — recent public trade (price, qty, side, timestamp)
- ExchangeInfo — trading rules, symbol filters, rate limits
"""

from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel


def _parse_decimal(v: Any) -> Decimal:
    """Convert string/int/float to Decimal via str() to avoid float precision loss.

    Raises ValueError (not decimal.InvalidOperation) so Pydantic wraps it in
    a ValidationError rather than letting the raw exception escape.
    """
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v))
    except Exception as exc:
        raise ValueError(f"invalid decimal value: {v!r}") from exc


# Annotated type that coerces any numeric-string field to Decimal.
DecimalStr = Annotated[Decimal, BeforeValidator(_parse_decimal)]


class Ticker(BaseModel):
    """24-hour rolling window price change statistics for a single trading pair.

    All price and volume fields are Decimal for financial precision.
    Field names use snake_case; camelCase aliases are accepted on input
    to match the raw MEXC API response.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    symbol: str
    price_change: DecimalStr
    price_change_percent: DecimalStr
    prev_close_price: DecimalStr
    last_price: DecimalStr
    bid_price: DecimalStr
    bid_qty: DecimalStr
    ask_price: DecimalStr
    ask_qty: DecimalStr
    open_price: DecimalStr
    high_price: DecimalStr
    low_price: DecimalStr
    volume: DecimalStr
    quote_volume: DecimalStr
    open_time: int
    close_time: int
    count: int | None = None
