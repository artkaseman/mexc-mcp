"""Integration tests for public market data tools.

Hits the live MEXC API — no API keys required.
Run with: make test-public
Skip in CI with: pytest -m "not integration"
"""

from decimal import Decimal

import pytest

from mexc_mcp.tools.market import get_exchange_info, get_klines, get_orderbook, get_ticker, ping_mexc

pytestmark = pytest.mark.integration


async def test_ping_mexc_live():
    result = await ping_mexc()
    assert result == "MEXC API is reachable."


async def test_get_ticker_live():
    result = await get_ticker("BTCUSDT")

    assert "error" not in result
    assert result["symbol"] == "BTCUSDT"
    assert Decimal(result["last_price"]) > 0
    assert Decimal(result["volume"]) > 0


async def test_get_orderbook_live():
    result = await get_orderbook("BTCUSDT", limit=5)

    assert "error" not in result
    assert len(result["bids"]) == 5
    assert len(result["asks"]) == 5
    # Best bid below best ask
    best_bid = Decimal(result["bids"][0][0])
    best_ask = Decimal(result["asks"][0][0])
    assert best_bid < best_ask


async def test_get_klines_live():
    result = await get_klines("BTCUSDT", "60m", limit=5)

    assert "error" not in result
    assert result["symbol"] == "BTCUSDT"
    assert result["interval"] == "60m"
    assert len(result["klines"]) == 5
    first = result["klines"][0]
    assert Decimal(first["high"]) >= Decimal(first["low"])
    assert first["close_time"] > first["open_time"]


async def test_get_exchange_info_live():
    result = await get_exchange_info("BTCUSDT")

    assert "error" not in result
    assert len(result["symbols"]) == 1
    sym = result["symbols"][0]
    assert sym["symbol"] == "BTCUSDT"
    assert sym["base_asset"] == "BTC"
    assert sym["is_spot_trading_allowed"] is True
