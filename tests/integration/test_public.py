"""Integration tests for public market data tools.

Hits the live MEXC API — no API keys required.
Run with: make test-public
Skip in CI with: pytest -m "not integration"
"""

import pytest

from mexc_mcp.tools.market import ping_mexc

pytestmark = pytest.mark.integration


async def test_ping_mexc_live():
    """GET /api/v3/ping succeeds against the real MEXC endpoint."""
    result = await ping_mexc()
    assert result == "MEXC API is reachable."
