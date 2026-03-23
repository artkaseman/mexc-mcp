"""MCP tools for MEXC wallet operations.

Requires authentication AND MEXC_ENABLE_WITHDRAWALS=true.
These tools interact with real funds — extra caution and explicit opt-in required.

Tools:
- get_deposit_address — blockchain deposit address and memo for a coin/network
- get_deposit_history — historical deposit records with optional filters
- get_withdraw_history — historical withdrawal records with optional filters
- internal_transfer   — move funds between spot and futures account types
"""
