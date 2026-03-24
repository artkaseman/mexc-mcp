"""MCP tools for MEXC public market data.

All tools in this module are available in every deployment mode (public, local, managed).
No authentication required. Tool docstrings are written as LLM-facing descriptions.

Tools:
- ping_mexc       — test connectivity to the MEXC API
- get_ticker      — 24-hour price change statistics for a symbol
- get_orderbook   — current bids and asks with configurable depth
- get_klines      — OHLCV candlestick data for a symbol and interval
- get_exchange_info — trading rules, symbol filters, and supported pairs
"""

from typing import Any

from mexc_mcp.client.base import MexcClient
from mexc_mcp.client.spot import SpotClient
from mexc_mcp.errors import MEXCAPIError
from mexc_mcp.models.market import ExchangeInfo, Kline, OrderBook, Ticker


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


async def get_orderbook(symbol: str, limit: int = 20) -> dict[str, Any]:
    """Get the current order book (bids and asks) for a trading pair.

    Returns the top N price levels on each side. Each level is [price, quantity].
    Bids are sorted highest-first; asks are sorted lowest-first.

    Args:
        symbol: Trading pair in uppercase, e.g. 'BTCUSDT'.
        limit:  Number of price levels per side. Allowed: 5, 10, 20, 50, 100,
                500, 1000. Default: 20.
    """
    try:
        async with MexcClient() as client:
            spot = SpotClient(client)
            raw = await spot.get_depth(symbol.upper(), limit)
        book = OrderBook.model_validate(raw)
        return book.model_dump(mode="json")
    except MEXCAPIError as exc:
        return {"error": exc.message, "code": exc.code}


async def get_klines(symbol: str, interval: str, limit: int = 100) -> dict[str, Any]:
    """Get OHLCV candlestick (kline) data for a trading pair.

    Each candle contains: open_time, open, high, low, close, volume,
    close_time, quote_volume.

    Args:
        symbol:   Trading pair in uppercase, e.g. 'BTCUSDT'.
        interval: Candle interval. Valid values: 1m, 5m, 15m, 30m, 60m,
                  4h, 1d, 1W, 1M. Note: use '60m' for 1-hour candles.
        limit:    Number of candles to return (default 100, max 1000).
    """
    try:
        async with MexcClient() as client:
            spot = SpotClient(client)
            raw = await spot.get_klines(symbol.upper(), interval, limit)
        klines = [Kline.model_validate(k) for k in raw]
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "klines": [k.model_dump(mode="json") for k in klines],
        }
    except MEXCAPIError as exc:
        return {"error": exc.message, "code": exc.code}


async def get_exchange_info(symbol: str) -> dict[str, Any]:
    """Get trading rules and symbol metadata from MEXC.

    Returns the symbol's status, base/quote assets, allowed order types,
    trading permissions, maker/taker commission rates, and price filters.

    Args:
        symbol: Trading pair in uppercase, e.g. 'BTCUSDT'.
    """
    try:
        async with MexcClient() as client:
            spot = SpotClient(client)
            raw = await spot.get_exchange_info(symbol.upper())
        info = ExchangeInfo.model_validate(raw)
        return info.model_dump(mode="json")
    except MEXCAPIError as exc:
        return {"error": exc.message, "code": exc.code}
