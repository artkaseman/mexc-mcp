"""MCP tools for MEXC public market data.

All tools in this module are available in every deployment mode (public, local, managed).
No authentication required. Tool docstrings are written as LLM-facing descriptions.

Tools:
- get_ticker      — 24-hour price change statistics for one or all symbols
- get_orderbook   — current bids and asks with configurable depth
- get_klines      — OHLCV candlestick data for a symbol and interval
- get_recent_trades — latest public trades for a symbol
- get_exchange_info — trading rules, symbol filters, and supported pairs
"""
