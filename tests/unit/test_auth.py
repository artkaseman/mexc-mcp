"""Unit tests for MEXC HMAC SHA256 request signing.

Tests:
- Signature generation produces correct HMAC SHA256 hex digest
- Timestamp is injected into query parameters
- Signature changes when any parameter changes
- Auth module never logs key values
"""
