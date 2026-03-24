"""Unit tests for Pydantic model validation.

Tests:
- Price/quantity string fields are coerced to Decimal on construction
- Invalid values raise ValidationError
- Model aliases handle MEXC's camelCase field naming
- Kline model_validator parses positional lists
- ExchangeInfo/SymbolInfo parse the full exchange payload
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from mexc_mcp.models.market import ExchangeInfo, Kline, OrderBook, Ticker


# ---------------------------------------------------------------------------
# Ticker
# ---------------------------------------------------------------------------


def test_ticker_parses_real_response(btcusdt_ticker_raw):
    ticker = Ticker.model_validate(btcusdt_ticker_raw)

    assert ticker.symbol == "BTCUSDT"
    assert ticker.last_price == Decimal("70996.79")
    assert ticker.high_price == Decimal("71810")
    assert ticker.volume == Decimal("15315.74637732")
    assert ticker.count is None


def test_ticker_decimal_precision(btcusdt_ticker_raw):
    """Decimal fields preserve full precision — no float rounding."""
    ticker = Ticker.model_validate(btcusdt_ticker_raw)

    assert ticker.bid_qty == Decimal("1.44656033")
    assert ticker.ask_qty == Decimal("0.00151758")
    assert ticker.quote_volume == Decimal("1068547727.91")


def test_ticker_camel_aliases(btcusdt_ticker_raw):
    ticker = Ticker.model_validate(btcusdt_ticker_raw)

    assert ticker.price_change == Decimal("3090.1")
    assert ticker.price_change_percent == Decimal("0.0455")
    assert ticker.prev_close_price == Decimal("67906.69")
    assert ticker.open_time == 1774310542044
    assert ticker.close_time == 1774310553112


def test_ticker_accepts_snake_case_keys():
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
    """Non-numeric price string raises ValidationError (not decimal.InvalidOperation)."""
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


# ---------------------------------------------------------------------------
# OrderBook
# ---------------------------------------------------------------------------


def test_orderbook_parses_real_response(btcusdt_depth_raw):
    book = OrderBook.model_validate(btcusdt_depth_raw)

    assert book.last_update_id == 66261959114
    assert book.timestamp == 1774311155172
    assert len(book.bids) == 5
    assert len(book.asks) == 5


def test_orderbook_bids_are_decimal_tuples(btcusdt_depth_raw):
    book = OrderBook.model_validate(btcusdt_depth_raw)

    price, qty = book.bids[0]
    assert isinstance(price, Decimal)
    assert isinstance(qty, Decimal)
    assert price == Decimal("70808.49")
    assert qty == Decimal("0.20819013")


def test_orderbook_asks_are_decimal_tuples(btcusdt_depth_raw):
    book = OrderBook.model_validate(btcusdt_depth_raw)

    price, qty = book.asks[0]
    assert price == Decimal("70808.50")
    assert qty == Decimal("0.63007237")


def test_orderbook_best_bid_less_than_best_ask(btcusdt_depth_raw):
    """Sanity check: best bid < best ask (no crossed book)."""
    book = OrderBook.model_validate(btcusdt_depth_raw)

    best_bid = book.bids[0][0]
    best_ask = book.asks[0][0]
    assert best_bid < best_ask


def test_orderbook_invalid_level_raises():
    with pytest.raises(ValidationError):
        OrderBook.model_validate({
            "lastUpdateId": 1,
            "bids": [["not-a-price", "1.0"]],
            "asks": [],
            "timestamp": 1,
        })


# ---------------------------------------------------------------------------
# Kline
# ---------------------------------------------------------------------------


def test_kline_parses_from_list(btcusdt_klines_raw):
    kline = Kline.model_validate(btcusdt_klines_raw[0])

    assert kline.open_time == 1774303200000
    assert kline.open == Decimal("70847.26")
    assert kline.high == Decimal("70896.52")
    assert kline.low == Decimal("70525.2")
    assert kline.close == Decimal("70791.25")
    assert kline.volume == Decimal("201.17259457")
    assert kline.close_time == 1774306800000
    assert kline.quote_volume == Decimal("14217200.73")


def test_kline_all_candles_parse(btcusdt_klines_raw):
    klines = [Kline.model_validate(k) for k in btcusdt_klines_raw]

    assert len(klines) == 3
    assert all(isinstance(k.open, Decimal) for k in klines)


def test_kline_integer_price_strings():
    """Whole-number price strings (e.g. '70990') parse to exact Decimal."""
    kline = Kline.model_validate(
        [1774306800000, "70791.25", "70990", "70409.65", "70902.7", "254.63750736", 1774310400000, "18004928.66"]
    )
    assert kline.high == Decimal("70990")


def test_kline_too_short_raises():
    with pytest.raises(ValidationError):
        Kline.model_validate([1, "1.0", "1.0"])  # only 3 elements


def test_kline_accepts_dict():
    """Kline also validates from a pre-built dict (populate_by_name path)."""
    kline = Kline.model_validate({
        "open_time": 1000,
        "open": "100.0",
        "high": "110.0",
        "low": "90.0",
        "close": "105.0",
        "volume": "50.0",
        "close_time": 2000,
        "quote_volume": "5250.0",
    })
    assert kline.high == Decimal("110.0")


# ---------------------------------------------------------------------------
# ExchangeInfo / SymbolInfo
# ---------------------------------------------------------------------------


def test_exchange_info_parses_real_response(btcusdt_exchange_info_raw):
    info = ExchangeInfo.model_validate(btcusdt_exchange_info_raw)

    assert info.timezone == "CST"
    assert info.server_time == 1774311163463
    assert len(info.symbols) == 1


def test_symbol_info_fields(btcusdt_exchange_info_raw):
    info = ExchangeInfo.model_validate(btcusdt_exchange_info_raw)
    sym = info.symbols[0]

    assert sym.symbol == "BTCUSDT"
    assert sym.base_asset == "BTC"
    assert sym.quote_asset == "USDT"
    assert sym.is_spot_trading_allowed is True
    assert sym.is_margin_trading_allowed is False
    assert sym.taker_commission == Decimal("0.0005")
    assert sym.maker_commission == Decimal("0")
    assert sym.full_name == "Bitcoin"


def test_symbol_info_order_types(btcusdt_exchange_info_raw):
    info = ExchangeInfo.model_validate(btcusdt_exchange_info_raw)
    sym = info.symbols[0]

    assert "LIMIT" in sym.order_types
    assert "MARKET" in sym.order_types


def test_symbol_info_filters_kept_raw(btcusdt_exchange_info_raw):
    """Filters are kept as raw dicts — no model parsing."""
    info = ExchangeInfo.model_validate(btcusdt_exchange_info_raw)
    sym = info.symbols[0]

    assert len(sym.filters) == 1
    assert sym.filters[0]["filterType"] == "PERCENT_PRICE_BY_SIDE"


def test_symbol_info_ignores_unknown_fields(btcusdt_exchange_info_raw):
    """extra='ignore' means unknown API fields don't cause ValidationError."""
    raw = btcusdt_exchange_info_raw.copy()
    raw["symbols"][0]["someNewFieldFromMEXC"] = "whatever"
    # Should not raise
    info = ExchangeInfo.model_validate(raw)
    assert info.symbols[0].symbol == "BTCUSDT"
