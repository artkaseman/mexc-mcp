"""MEXC Wallet API client methods.

Covers deposit/withdrawal operations and internal transfers:
- Deposit records and deposit address lookup
- Withdrawal submission and status tracking
- Internal transfer between account types (spot ↔ futures)

All wallet endpoints require authentication. This module is only instantiated
when MEXC_ENABLE_WITHDRAWALS=true is set (enforced in modes.py / config.py).
"""
