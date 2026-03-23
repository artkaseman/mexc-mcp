"""MEXC API client package.

Standalone async HTTP client for the MEXC exchange REST API.
Zero MCP awareness — importable and testable without FastMCP.

Submodules:
- auth    — HMAC SHA256 request signing and timestamp management
- base    — Async httpx client, rate limit tracking, retry logic
- spot    — Spot v3 API methods (market data, trading, account)
- futures — Futures v1 API methods (contracts, positions, orders)
- wallet  — Wallet endpoints (deposits, withdrawals, transfers)
"""
