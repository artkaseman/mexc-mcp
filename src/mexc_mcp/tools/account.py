"""MCP tools for MEXC account queries.

Requires authentication. Available in local and managed modes only.
These tools are read-only — they never place or modify orders.

Tools:
- get_balances     — spot wallet asset balances (free and locked)
- get_open_orders  — currently open orders, optionally filtered by symbol
- get_order        — status and fill details for a specific order ID
- get_trade_history — executed trades for a symbol with optional time range
"""
