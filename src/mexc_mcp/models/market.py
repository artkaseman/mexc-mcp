"""Pydantic models for MEXC market data API responses.

Covers:
- Ticker24hr  — 24-hour rolling window price change statistics
- OrderBook   — bids/asks as (price, quantity) Decimal pairs
- Kline       — OHLCV candlestick data
- Trade       — recent public trade (price, qty, side, timestamp)
- ExchangeInfo — trading rules, symbol filters, rate limits
"""
