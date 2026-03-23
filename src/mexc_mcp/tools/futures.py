"""MCP tools for MEXC Futures operations.

Requires authentication. Available in local and managed modes only.
Trading tools within this module additionally require MEXC_ENABLE_TRADING=true.

Tools:
- get_contracts      — list available perpetual contracts and their specifications
- get_positions      — current open futures positions with PnL
- get_funding_rate   — current and historical funding rate for a contract
- place_futures_order — open or close a futures position
- cancel_futures_order — cancel an open futures order
"""
