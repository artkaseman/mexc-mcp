"""Integration tests for authenticated MEXC API client methods.

Requires MEXC_API_KEY and MEXC_SECRET_KEY in environment or .env file.
Hits the live API — use read-only endpoints where possible to avoid side effects.

Tests:
- Account balance endpoint returns a list of Balance models
- Open orders query succeeds (may return empty list on a fresh account)
- Signature validation: tampered signature returns AuthError
"""
