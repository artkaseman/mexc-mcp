"""Pydantic models for MEXC market data API responses.

Covers:
- Ticker      — 24-hour rolling window price change statistics
- OrderBook   — bids/asks as (price, quantity) Decimal pairs
- Kline       — OHLCV candlestick data (parsed from positional list)
- SymbolInfo  — per-symbol trading rules from exchangeInfo
- ExchangeInfo — server metadata + list of SymbolInfo
"""

from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, model_validator
from pydantic.alias_generators import to_camel


# ---------------------------------------------------------------------------
# Shared Decimal coercion
# ---------------------------------------------------------------------------


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

# camelCase config shared by models whose fields map directly from MEXC JSON objects.
_CAMEL_CONFIG = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------------------------------------------------------------------------
# Ticker
# ---------------------------------------------------------------------------


class Ticker(BaseModel):
    """24-hour rolling window price change statistics for a single trading pair.

    All price and volume fields are Decimal for financial precision.
    Field names use snake_case; camelCase aliases are accepted on input
    to match the raw MEXC API response.
    """

    model_config = _CAMEL_CONFIG

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


# ---------------------------------------------------------------------------
# OrderBook
# ---------------------------------------------------------------------------


def _parse_levels(v: Any) -> list[tuple[Decimal, Decimal]]:
    """Parse a list of [price_str, qty_str] pairs into (Decimal, Decimal) tuples."""
    if not isinstance(v, list):
        raise ValueError(f"expected list of price levels, got {type(v)}")
    result = []
    for item in v:
        try:
            price, qty = item[0], item[1]
            result.append((_parse_decimal(price), _parse_decimal(qty)))
        except Exception as exc:
            raise ValueError(f"invalid order book level {item!r}") from exc
    return result


OrderLevels = Annotated[list[tuple[Decimal, Decimal]], BeforeValidator(_parse_levels)]


class OrderBook(BaseModel):
    """Current order book snapshot for a trading pair.

    bids and asks are lists of (price, quantity) Decimal tuples, ordered
    best-first (highest bid, lowest ask).
    """

    model_config = _CAMEL_CONFIG

    last_update_id: int
    bids: OrderLevels
    asks: OrderLevels
    timestamp: int


# ---------------------------------------------------------------------------
# Kline
# ---------------------------------------------------------------------------


class Kline(BaseModel):
    """A single OHLCV candlestick from the MEXC klines endpoint.

    MEXC returns klines as positional lists:
      [openTime, open, high, low, close, volume, closeTime, quoteVolume]

    The model_validator converts the list to named fields before validation.
    """

    open_time: int
    open: DecimalStr
    high: DecimalStr
    low: DecimalStr
    close: DecimalStr
    volume: DecimalStr
    close_time: int
    quote_volume: DecimalStr

    @model_validator(mode="before")
    @classmethod
    def from_list(cls, v: Any) -> Any:
        """Accept either a positional list (raw API) or a dict (already parsed)."""
        if isinstance(v, (list, tuple)):
            if len(v) < 8:
                raise ValueError(f"kline list too short: expected ≥8 elements, got {len(v)}")
            return {
                "open_time": v[0],
                "open": v[1],
                "high": v[2],
                "low": v[3],
                "close": v[4],
                "volume": v[5],
                "close_time": v[6],
                "quote_volume": v[7],
            }
        return v


# ---------------------------------------------------------------------------
# ExchangeInfo
# ---------------------------------------------------------------------------


class SymbolInfo(BaseModel):
    """Trading rules and metadata for a single symbol from exchangeInfo."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",  # MEXC adds new fields periodically; ignore unknowns
    )

    symbol: str
    status: str  # "1" = trading
    base_asset: str
    base_asset_precision: int
    quote_asset: str
    quote_asset_precision: int
    order_types: list[str]
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    permissions: list[str]
    maker_commission: DecimalStr
    taker_commission: DecimalStr
    base_size_precision: DecimalStr
    full_name: str
    filters: list[dict[str, Any]]  # shape varies by filterType; kept raw


class ExchangeInfo(BaseModel):
    """MEXC exchange metadata and per-symbol trading rules."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    timezone: str
    server_time: int
    symbols: list[SymbolInfo]
