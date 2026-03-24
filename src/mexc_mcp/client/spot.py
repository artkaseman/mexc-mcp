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

    Wraps MexcClient and returns raw dicts. Callers are responsible for
    validating responses into Pydantic models.
    """

    def __init__(self, client: MexcClient) -> None:
        self._client = client

    async def get_ticker_24hr(self, symbol: str) -> dict:  # type: ignore[type-arg]
        """GET /api/v3/ticker/24hr — 24-hour rolling window stats for one symbol."""
        return await self._client.get("/api/v3/ticker/24hr", params={"symbol": symbol})
