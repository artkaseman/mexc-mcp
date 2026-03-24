"""MEXC Spot v3 API client methods.

Maps 1:1 to the Spot v3 documentation sections:
- Market data: ping, time, exchange info, depth, trades, klines, ticker
- Account: balances, trade history, open orders, order status
- Trading: place order, cancel order, cancel all open orders

Base URL: https://api.mexc.com
Reference: https://mexcdevelop.github.io/apidocs/spot_v3_en/
"""

from mexc_mcp.client.base import MexcClient


class SpotClient:
    """Typed methods for the MEXC Spot v3 REST API.

    Wraps MexcClient and returns raw dicts/lists. Callers are responsible for
    validating responses into Pydantic models.
    """

    def __init__(self, client: MexcClient) -> None:
        self._client = client

    async def get_ticker_24hr(self, symbol: str) -> dict:  # type: ignore[type-arg]
        """GET /api/v3/ticker/24hr — 24-hour rolling window stats for one symbol."""
        return await self._client.get("/api/v3/ticker/24hr", params={"symbol": symbol})

    async def get_depth(self, symbol: str, limit: int = 20) -> dict:  # type: ignore[type-arg]
        """GET /api/v3/depth — order book snapshot.

        limit: number of price levels per side. Supported: 5, 10, 20, 50, 100, 500, 1000.
        """
        return await self._client.get(
            "/api/v3/depth", params={"symbol": symbol, "limit": str(limit)}
        )

    async def get_klines(self, symbol: str, interval: str, limit: int = 100) -> list:  # type: ignore[type-arg]
        """GET /api/v3/klines — OHLCV candlestick data.

        interval: 1m | 5m | 15m | 30m | 60m | 4h | 1d | 1W | 1M
        limit: number of candles (default 100, max 1000).
        """
        return await self._client.get(  # type: ignore[return-value]
            "/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": str(limit)},
        )

    async def get_exchange_info(self, symbol: str) -> dict:  # type: ignore[type-arg]
        """GET /api/v3/exchangeInfo — trading rules for a symbol."""
        return await self._client.get("/api/v3/exchangeInfo", params={"symbol": symbol})

    async def get_account(self) -> dict:  # type: ignore[type-arg]
        """GET /api/v3/account — account info including spot balances. Requires auth."""
        return await self._client.signed_get("/api/v3/account")
