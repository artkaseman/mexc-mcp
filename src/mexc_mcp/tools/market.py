"""MCP tools for MEXC public market data.

All tools in this module are available in every deployment mode (public, local, managed).
No authentication required. Tool docstrings are written as LLM-facing descriptions.

Tools:
- ping_mexc       — test connectivity to the MEXC API
- get_ticker      — 24-hour price change statistics for a symbol
- get_orderbook   — current bids and asks with configurable depth
- get_klines      — OHLCV candlestick data for a symbol and interval
- get_recent_trades — latest public trades for a symbol
- get_exchange_info — trading rules, symbol filters, and supported pairs
"""

from typing import Any

from mexc_mcp.client.base import MexcClient
from mexc_mcp.client.spot import SpotClient
from mexc_mcp.errors import MEXCAPIError
from mexc_mcp.models.market import Ticker


async def ping_mexc() -> str:
    """Test connectivity to the MEXC API.

    Sends a lightweight request to MEXC and confirms the API is reachable.
    Use this to verify network connectivity before calling data or trading tools.
    Returns a confirmation message on success, or raises an error if the API
    is unreachable.
    """
    try:
        async with MexcClient() as client:
            await client.get("/api/v3/ping")
        return "MEXC API is reachable."
    except MEXCAPIError as exc:
        return f"MEXC API error: {exc.message}"


async def get_ticker(symbol: str) -> dict[str, Any]:
    """Get 24-hour rolling price statistics for a trading pair.

    Returns price change, percentage change, open/high/low/close prices,
    bid/ask prices and quantities, and trading volume for the past 24 hours.

    Args:
        symbol: Trading pair in uppercase, e.g. 'BTCUSDT', 'ETHUSDT', 'SOLUSDT'.

    Returns a dict with fields: symbol, lastPrice, highPrice, lowPrice,
    priceChange, priceChangePercent, volume, quoteVolume, bidPrice, askPrice.
    """
    try:
        async with MexcClient() as client:
            spot = SpotClient(client)
            raw = await spot.get_ticker_24hr(symbol.upper())
        ticker = Ticker.model_validate(raw)
        return ticker.model_dump(mode="json")
    except MEXCAPIError as exc:
        return {"error": exc.message, "code": exc.code}
