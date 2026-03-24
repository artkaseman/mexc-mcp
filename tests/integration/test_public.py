"""Integration tests for public market data tools.

Hits the live MEXC API — no API keys required.
Run with: make test-public
Skip in CI with: pytest -m "not integration"
"""

import pytest

from mexc_mcp.tools.market import get_ticker, ping_mexc

pytestmark = pytest.mark.integration


async def test_ping_mexc_live():
    """GET /api/v3/ping succeeds against the real MEXC endpoint."""
    result = await ping_mexc()
    assert result == "MEXC API is reachable."


async def test_get_ticker_live():
    """GET /api/v3/ticker/24hr returns valid 24h stats for BTCUSDT."""
    result = await get_ticker("BTCUSDT")

    assert "error" not in result
    assert result["symbol"] == "BTCUSDT"
    # lastPrice must be a non-zero positive number
    from decimal import Decimal
    assert Decimal(result["last_price"]) > 0
    assert Decimal(result["volume"]) > 0
