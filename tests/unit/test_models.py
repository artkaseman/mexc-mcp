"""Unit tests for Pydantic model validation.

Tests:
- Price/quantity string fields are coerced to Decimal on construction
- Invalid values raise ValidationError with descriptive messages
- Model aliases handle MEXC's camelCase field naming
- Edge cases: null count, integer price strings (no decimal point)
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from mexc_mcp.models.market import Ticker


def test_ticker_parses_real_response(btcusdt_ticker_raw):
    """Ticker model validates successfully against a real MEXC response."""
    ticker = Ticker.model_validate(btcusdt_ticker_raw)

    assert ticker.symbol == "BTCUSDT"
    assert ticker.last_price == Decimal("70996.79")
    assert ticker.high_price == Decimal("71810")
    assert ticker.volume == Decimal("15315.74637732")
    assert ticker.count is None


def test_ticker_decimal_precision(btcusdt_ticker_raw):
    """Decimal fields preserve full precision — no float rounding."""
    ticker = Ticker.model_validate(btcusdt_ticker_raw)

    # bid_qty has 8 decimal places — float would lose precision here
    assert ticker.bid_qty == Decimal("1.44656033")
    assert ticker.ask_qty == Decimal("0.00151758")
    assert ticker.quote_volume == Decimal("1068547727.91")


def test_ticker_camel_aliases(btcusdt_ticker_raw):
    """camelCase API keys map to snake_case model attributes."""
    ticker = Ticker.model_validate(btcusdt_ticker_raw)

    assert ticker.price_change == Decimal("3090.1")
    assert ticker.price_change_percent == Decimal("0.0455")
    assert ticker.prev_close_price == Decimal("67906.69")
    assert ticker.open_time == 1774310542044
    assert ticker.close_time == 1774310553112


def test_ticker_accepts_snake_case_keys(btcusdt_ticker_raw):
    """Model also accepts snake_case keys (populate_by_name=True)."""
    snake = {
        "symbol": "BTCUSDT",
        "price_change": "100.0",
        "price_change_percent": "0.15",
        "prev_close_price": "67000.0",
        "last_price": "67100.0",
        "bid_price": "67099.0",
        "bid_qty": "0.5",
        "ask_price": "67101.0",
        "ask_qty": "0.3",
        "open_price": "67000.0",
        "high_price": "67500.0",
        "low_price": "66800.0",
        "volume": "100.0",
        "quote_volume": "6710000.0",
        "open_time": 1000000,
        "close_time": 1000001,
    }
    ticker = Ticker.model_validate(snake)
    assert ticker.last_price == Decimal("67100.0")


def test_ticker_invalid_price_raises():
    """Non-numeric price string raises ValidationError."""
    bad = {
        "symbol": "BTCUSDT",
        "priceChange": "not-a-number",
        "priceChangePercent": "0.0",
        "prevClosePrice": "1.0",
        "lastPrice": "1.0",
        "bidPrice": "1.0",
        "bidQty": "1.0",
        "askPrice": "1.0",
        "askQty": "1.0",
        "openPrice": "1.0",
        "highPrice": "1.0",
        "lowPrice": "1.0",
        "volume": "1.0",
        "quoteVolume": "1.0",
        "openTime": 1,
        "closeTime": 2,
    }
    with pytest.raises(ValidationError):
        Ticker.model_validate(bad)
