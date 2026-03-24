"""Unit tests for server mode and tool registration logic.

Uses FastMCP Client in-process (Client(mcp)) — no HTTP server, no network.
"""

import pytest
from fastmcp import Client

from mexc_mcp.modes import ServerMode, register_tools
from mexc_mcp.server import build_server

EXPECTED_PUBLIC_TOOLS = {
    "ping_mexc",
    "get_ticker",
    "get_orderbook",
    "get_klines",
    "get_exchange_info",
}


async def test_public_mode_registers_exactly_public_tools():
    mcp = build_server(ServerMode.PUBLIC)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools} == EXPECTED_PUBLIC_TOOLS


async def test_local_mode_contains_all_public_tools():
    """Local mode is a superset of public mode."""
    mcp = build_server(ServerMode.LOCAL)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = {t.name for t in tools}
    assert EXPECTED_PUBLIC_TOOLS.issubset(names)


async def test_tool_schemas_have_descriptions():
    """Every registered tool must have a non-empty description (LLM-facing docstring)."""
    mcp = build_server(ServerMode.PUBLIC)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    for tool in tools:
        assert tool.description, f"tool {tool.name!r} has no description"


async def test_get_ticker_schema_has_symbol_param():
    mcp = build_server(ServerMode.PUBLIC)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    ticker = next(t for t in tools if t.name == "get_ticker")
    params = ticker.inputSchema.get("properties", {})
    assert "symbol" in params


async def test_get_orderbook_schema_has_limit_param():
    mcp = build_server(ServerMode.PUBLIC)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    book = next(t for t in tools if t.name == "get_orderbook")
    params = book.inputSchema.get("properties", {})
    assert "symbol" in params
    assert "limit" in params


async def test_invalid_mode_string_raises():
    with pytest.raises(ValueError):
        ServerMode("invalid_mode")
