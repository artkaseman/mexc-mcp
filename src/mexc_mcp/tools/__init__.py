"""MCP tool registry — exports tool groups by capability tier.

Tool groups are imported by modes.py to selectively register tools
with the FastMCP app based on the active deployment mode.

Exported groups:
- PUBLIC_TOOLS        — market data tools; available in all modes
- AUTHENTICATED_TOOLS — account query tools; local + managed only
- TRADING_TOOLS       — order placement/cancellation; requires MEXC_ENABLE_TRADING=true
- WALLET_TOOLS        — deposit/withdraw/transfer; requires MEXC_ENABLE_WITHDRAWALS=true
- FUTURES_TOOLS       — futures positions, orders, funding; local + managed only
"""

from collections.abc import Callable
from typing import Any

from mexc_mcp.tools.account import get_balances
from mexc_mcp.tools.market import get_exchange_info, get_klines, get_orderbook, get_ticker, ping_mexc

PUBLIC_TOOLS: list[Callable[..., Any]] = [ping_mexc, get_ticker, get_orderbook, get_klines, get_exchange_info]
AUTHENTICATED_TOOLS: list[Callable[..., Any]] = [get_balances]
TRADING_TOOLS: list[Callable[..., Any]] = []
WALLET_TOOLS: list[Callable[..., Any]] = []
FUTURES_TOOLS: list[Callable[..., Any]] = []
