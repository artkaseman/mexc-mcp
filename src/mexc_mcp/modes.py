"""Server deployment modes and tool registration logic.

Defines the ServerMode enum (public, local, managed) and the function that
registers the appropriate tool groups with the FastMCP app for each mode.

This module is the security boundary: authenticated tools are never registered
in public mode — they cannot be discovered or called by a connected LLM client.
"""

from enum import StrEnum

from fastmcp import FastMCP


class ServerMode(StrEnum):
    PUBLIC = "public"
    LOCAL = "local"
    MANAGED = "managed"


def register_tools(mcp: FastMCP, mode: ServerMode) -> None:
    """Register the correct tool groups for the given deployment mode.

    Public  → PUBLIC_TOOLS only.
    Local   → PUBLIC_TOOLS + AUTHENTICATED_TOOLS + optionally TRADING/WALLET/FUTURES.
    Managed → same as local, plus audit logging (future).
    """
    from mexc_mcp.tools import (
        AUTHENTICATED_TOOLS,
        FUTURES_TOOLS,
        PUBLIC_TOOLS,
        TRADING_TOOLS,
        WALLET_TOOLS,
    )

    for fn in PUBLIC_TOOLS:
        mcp.add_tool(fn)

    if mode in (ServerMode.LOCAL, ServerMode.MANAGED):
        for fn in AUTHENTICATED_TOOLS:
            mcp.add_tool(fn)
        for fn in FUTURES_TOOLS:
            mcp.add_tool(fn)
        # Trading and wallet tools require explicit opt-in via env flags.
        # Config enforcement happens in config.py; modes.py receives
        # pre-filtered lists once those modules are implemented.
        for fn in TRADING_TOOLS:
            mcp.add_tool(fn)
        for fn in WALLET_TOOLS:
            mcp.add_tool(fn)
