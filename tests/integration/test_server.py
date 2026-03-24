"""Integration tests for full MCP protocol round-trips.

Two test classes:
- In-process tests: Client(mcp) — verify MCP protocol without a network server.
  These run fast and cover tool calls end-to-end via respx-mocked HTTP.

- HTTP server tests: start a real uvicorn server, connect via
  Client("http://...") — the same path MCP Inspector takes.
  This verifies --transport http works and that any MCP client (including
  Inspector) can list tools and call them over the wire.

To test manually with MCP Inspector:
  uv run python -m mexc_mcp.server --mode public --transport http --port 8000
  npx @modelcontextprotocol/inspector http://localhost:8000/mcp
"""

import asyncio
import socket

import httpx
import pytest
import respx
import uvicorn
from fastmcp import Client


from mexc_mcp.modes import ServerMode
from mexc_mcp.server import build_server

pytestmark = pytest.mark.integration

EXPECTED_PUBLIC_TOOLS = {
    "ping_mexc",
    "get_ticker",
    "get_orderbook",
    "get_klines",
    "get_exchange_info",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _free_port() -> int:
    """Ask the OS for a free TCP port. Closed before returning; small race window."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ---------------------------------------------------------------------------
# In-process MCP protocol tests (Client(mcp), no real HTTP server)
# ---------------------------------------------------------------------------


async def test_in_process_lists_public_tools():
    """Public-mode FastMCP instance advertises all expected tools."""
    mcp = build_server(ServerMode.PUBLIC)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == EXPECTED_PUBLIC_TOOLS


async def test_in_process_ping_tool_call():
    """ping_mexc returns the expected message when called via MCP protocol."""
    mcp = build_server(ServerMode.PUBLIC)
    with respx.mock(base_url="https://api.mexc.com", assert_all_called=False) as mock:
        mock.get("/api/v3/ping").mock(return_value=httpx.Response(200, json={}))
        async with Client(mcp) as client:
            result = await client.call_tool("ping_mexc", {})
    assert "reachable" in str(result).lower()


async def test_in_process_get_ticker_tool_call(btcusdt_ticker_raw):
    """get_ticker returns validated Ticker data when called via MCP protocol."""
    mcp = build_server(ServerMode.PUBLIC)
    with respx.mock(base_url="https://api.mexc.com", assert_all_called=False) as mock:
        mock.get("/api/v3/ticker/24hr").mock(
            return_value=httpx.Response(200, json=btcusdt_ticker_raw)
        )
        async with Client(mcp) as client:
            result = await client.call_tool("get_ticker", {"symbol": "BTCUSDT"})
    text = str(result)
    assert "BTCUSDT" in text
    assert "70996.79" in text


# ---------------------------------------------------------------------------
# HTTP transport tests (real uvicorn server + Client over HTTP)
# ---------------------------------------------------------------------------


@pytest.fixture
async def public_http_url():
    """Start the public-mode FastMCP HTTP server on a free port.

    Polls server.started rather than sleeping a fixed duration.
    Yields the MCP endpoint URL, then shuts the server down cleanly.
    """
    port = _free_port()
    mcp = build_server(ServerMode.PUBLIC)
    app = mcp.http_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())

    # Wait until uvicorn reports it is ready (polls every 50 ms, 5 s timeout)
    for _ in range(100):
        if server.started:
            break
        await asyncio.sleep(0.05)
    else:
        server.should_exit = True
        await task
        pytest.fail("HTTP server did not start within 5 seconds")

    yield f"http://127.0.0.1:{port}/mcp"

    server.should_exit = True
    await task


async def test_http_transport_lists_tools(public_http_url):
    """MCP Inspector path: FastMCP Client over HTTP lists all expected tools."""
    async with Client(public_http_url) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == EXPECTED_PUBLIC_TOOLS


async def test_http_transport_ping_tool_call(public_http_url):
    """ping_mexc is callable via the HTTP transport (same as MCP Inspector would call it).

    This test hits the real MEXC API — no mock — to verify the full chain:
    HTTP client → uvicorn → FastMCP → tool → MEXC API.
    """
    async with Client(public_http_url) as client:
        result = await client.call_tool("ping_mexc", {})
    assert "reachable" in str(result).lower()


async def test_http_transport_unknown_tool_raises(public_http_url):
    """Calling a non-existent tool raises an error (not a server crash)."""
    async with Client(public_http_url) as client:
        with pytest.raises(Exception):
            await client.call_tool("does_not_exist", {})
