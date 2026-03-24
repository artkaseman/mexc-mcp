"""MCP tools for MEXC account queries.

Requires authentication. Available in local and managed modes only.
These tools are read-only — they never place or modify orders.

Tools:
- get_balances     — spot wallet asset balances (free and locked)
- get_open_orders  — currently open orders, optionally filtered by symbol
- get_order        — status and fill details for a specific order ID
- get_trade_history — executed trades for a symbol with optional time range
"""

from typing import Any

from mexc_mcp.client.auth import RequestSigner
from mexc_mcp.client.base import MexcClient
from mexc_mcp.client.spot import SpotClient
from mexc_mcp.config import get_settings
from mexc_mcp.errors import MEXCAPIError
from mexc_mcp.models.account import AccountInfo


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
        settings = get_settings()
        signer = RequestSigner(
            api_key=settings.mexc_api_key,
            secret_key=settings.mexc_secret_key,
        )
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
