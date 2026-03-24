"""MCP tools for MEXC account queries.

Requires authentication. Available in local and managed modes only.
These tools are read-only — they never place or modify orders.

Tools:
- get_balances      — spot wallet asset balances (free and locked)
- get_open_orders   — currently open orders, optionally filtered by symbol
- get_trade_history — executed trades for a symbol with optional time range
"""

from typing import Any

from mexc_mcp.client.auth import RequestSigner
from mexc_mcp.client.base import MexcClient
from mexc_mcp.client.spot import SpotClient
from mexc_mcp.config import get_settings
from mexc_mcp.errors import MEXCAPIError
from mexc_mcp.models.account import AccountInfo, Order, TradeRecord


def _make_signer() -> RequestSigner:
    """Build a RequestSigner from environment credentials.

    Raises ValueError if MEXC_API_KEY or MEXC_SECRET_KEY are not set.
    """
    settings = get_settings()
    return RequestSigner(
        api_key=settings.mexc_api_key,
        secret_key=settings.mexc_secret_key,
    )


async def get_balances() -> dict[str, Any]:
    """Get spot wallet balances for all assets with non-zero holdings.

    Returns free (available) and locked (in open orders) quantities for
    every asset that has a non-zero balance. Zero-balance assets are omitted.

    Requires MEXC_API_KEY and MEXC_SECRET_KEY to be set in the environment
    or .env file. Use this tool to check available funds before trading.

    Returns a dict with:
      account_type: always 'SPOT'
      can_trade:    whether trading is enabled on this API key
      balances:     list of {asset, free, locked} for non-zero holdings
    """
    try:
        signer = _make_signer()
        async with MexcClient(signer=signer) as client:
            spot = SpotClient(client)
            raw = await spot.get_account()
        account = AccountInfo.model_validate(raw)
        nonzero = [b for b in account.balances if b.free > 0 or b.locked > 0]
        return {
            "account_type": account.account_type,
            "can_trade": account.can_trade,
            "balances": [b.model_dump(mode="json") for b in nonzero],
        }
    except ValueError as exc:
        return {"error": f"Authentication not configured: {exc}"}
    except MEXCAPIError as exc:
        return {"error": exc.message, "code": exc.code}


async def get_open_orders(symbol: str | None = None) -> dict[str, Any]:
    """Get all currently open (unfilled or partially filled) orders.

    Args:
        symbol: Trading pair to filter by, e.g. 'BTCUSDT'. If omitted,
                returns open orders across all trading pairs. Note: querying
                all pairs is heavier — prefer filtering by symbol when possible.

    Returns a dict with:
      symbol: the requested symbol, or 'ALL' if none was specified
      orders: list of open orders, each with fields: order_id, symbol, side,
              type, price, orig_qty, executed_qty, status, time, update_time
    """
    try:
        signer = _make_signer()
        async with MexcClient(signer=signer) as client:
            spot = SpotClient(client)
            raw_list = await spot.get_open_orders(symbol.upper() if symbol else None)
        orders = [Order.model_validate(o) for o in raw_list]
        return {
            "symbol": symbol.upper() if symbol else "ALL",
            "orders": [o.model_dump(mode="json") for o in orders],
        }
    except ValueError as exc:
        return {"error": f"Authentication not configured: {exc}"}
    except MEXCAPIError as exc:
        return {"error": exc.message, "code": exc.code}


async def get_trade_history(
    symbol: str,
    limit: int = 500,
    start_time: int | None = None,
    end_time: int | None = None,
) -> dict[str, Any]:
    """Get executed trade history for a trading pair.

    Returns trades where your orders were filled, including the price,
    quantity, and fee paid. Useful for P&L tracking and reconciliation.

    Args:
        symbol:     Trading pair in uppercase, e.g. 'BTCUSDT'.
        limit:      Maximum number of trades to return (default 500, max 1000).
        start_time: Start of time range as Unix timestamp in milliseconds (optional).
        end_time:   End of time range as Unix timestamp in milliseconds (optional).

    Returns a dict with:
      symbol: the trading pair
      trades: list of trades, each with: id, order_id, price, qty, quote_qty,
              commission, commission_asset, time, is_buyer, is_maker
    """
    try:
        signer = _make_signer()
        async with MexcClient(signer=signer) as client:
            spot = SpotClient(client)
            raw_list = await spot.get_my_trades(
                symbol.upper(), limit=limit, start_time=start_time, end_time=end_time
            )
        trades = [TradeRecord.model_validate(t) for t in raw_list]
        return {
            "symbol": symbol.upper(),
            "trades": [t.model_dump(mode="json") for t in trades],
        }
    except ValueError as exc:
        return {"error": f"Authentication not configured: {exc}"}
    except MEXCAPIError as exc:
        return {"error": exc.message, "code": exc.code}
