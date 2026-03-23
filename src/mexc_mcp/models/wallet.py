"""Pydantic models for MEXC Wallet API responses.

Covers:
- DepositAddress  — blockchain address and memo/tag for a given coin/network
- DepositRecord   — historical deposit entry (amount, coin, network, status, txid)
- WithdrawRecord  — historical withdrawal entry (amount, fee, coin, network, status)
- Transfer        — internal transfer record between account types (spot ↔ futures)
"""
