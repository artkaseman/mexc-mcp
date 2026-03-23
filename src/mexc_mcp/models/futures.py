"""Pydantic models for MEXC Futures API responses.

Covers:
- Contract    — perpetual contract specification (tick size, lot size, leverage caps)
- Position    — open position (side, size, entry price, unrealized PnL, liquidation price)
- FundingRate — current and historical funding rate for a contract
- FuturesOrder — futures order object with margin mode and leverage fields
"""
