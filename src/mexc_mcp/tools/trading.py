"""MCP tools for spot order placement and cancellation.

Requires authentication AND MEXC_ENABLE_TRADING=true.
All tool calls are logged with full parameters via structlog before execution.

Tools:
- place_order      — submit a new spot order (limit or market)
- cancel_order     — cancel a specific open order by ID
- cancel_all_orders — cancel all open orders for a symbol
"""
