"""FastMCP server entry point.

Reads the --mode flag (defaults to 'public'), instantiates the FastMCP app,
delegates tool registration to modes.py, and starts the appropriate transport:
- stdio   for local mode (subprocess, Claude Desktop)
- HTTP    for public/managed mode (remote, streamable)

This module is intentionally thin — it is pure wiring. No business logic lives here.
"""

import argparse

import structlog
from fastmcp import FastMCP

from mexc_mcp.modes import ServerMode, register_tools

logger = structlog.get_logger()


def build_server(mode: ServerMode) -> FastMCP:
    """Construct and configure the FastMCP app for the given mode."""
    mcp = FastMCP("mexc-mcp")
    register_tools(mcp, mode)
    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MEXC MCP server — exposes MEXC exchange tools via the Model Context Protocol."
    )
    parser.add_argument(
        "--mode",
        type=ServerMode,
        default=ServerMode.PUBLIC,
        choices=list(ServerMode),
        help="Deployment mode: public (market data only), local (full suite), managed (B2B). Default: public.",
    )
    args = parser.parse_args()

    log = logger.bind(mode=args.mode.value)
    log.info("starting mexc-mcp server")

    mcp = build_server(args.mode)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
