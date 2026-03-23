"""Unit tests for MCP tool input/output contracts.

Uses respx to intercept httpx requests — no real network calls.
"""

import httpx
import pytest

from mexc_mcp.errors import MEXCAPIError
from mexc_mcp.tools.market import ping_mexc


async def test_ping_mexc_success(mexc_mock):
    """ping_mexc returns a reachability message on HTTP 200."""
    mexc_mock.get("/api/v3/ping").mock(return_value=httpx.Response(200, json={}))

    result = await ping_mexc()

    assert "reachable" in result.lower()


async def test_ping_mexc_server_error(mexc_mock):
    """ping_mexc surfaces the MEXC error message on HTTP 500."""
    mexc_mock.get("/api/v3/ping").mock(
        return_value=httpx.Response(500, json={"code": -1, "msg": "internal server error"})
    )

    result = await ping_mexc()

    assert "error" in result.lower()


async def test_ping_mexc_rate_limited(mexc_mock):
    """ping_mexc surfaces a rate-limit error on HTTP 429."""
    mexc_mock.get("/api/v3/ping").mock(return_value=httpx.Response(429))

    result = await ping_mexc()

    assert "error" in result.lower()
