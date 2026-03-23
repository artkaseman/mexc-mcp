"""Integration tests for public market data tools.

Hits the live MEXC API — no API keys required. Mark with pytest.mark.public_only
so these can be run independently of authenticated tests.

Tests:
- get_ticker returns valid 24h stats for BTCUSDT
- get_orderbook returns non-empty bids and asks
- get_klines returns OHLCV data for a valid symbol/interval
- get_exchange_info lists at least one trading symbol
"""
