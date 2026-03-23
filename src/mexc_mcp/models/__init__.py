"""Pydantic v2 models for MEXC API request parameters and response payloads.

All models use model_config aliases to handle MEXC's inconsistent casing.
All price/quantity fields use Decimal (never float) for financial precision,
enforced via custom validators on fields that arrive as strings from the API.

Submodules:
- common  — Shared types: Symbol, OrderSide, OrderType, TimeInForce
- market  — Market data: Ticker, OrderBook, Kline, Trade
- account — Account data: Balance, Order, TradeHistory
- futures — Futures data: Position, FundingRate, Contract
- wallet  — Wallet data: DepositRecord, WithdrawRecord, Transfer
"""
