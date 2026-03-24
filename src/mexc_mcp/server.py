"""FastMCP server entry point.

Reads the --mode and --transport flags, instantiates the FastMCP app,
delegates tool registration to modes.py, and starts the appropriate transport:
- stdio   — for local mode (subprocess, Claude Desktop)
- http    — for public/managed mode (remote, streamable HTTP on /mcp)

This module is intentionally thin — it is pure wiring. No business logic lives here.

Usage examples:
  # Local stdio (Claude Desktop):
  uv run python -m mexc_mcp.server --mode local

  # Public HTTP (remote deployment):
  uv run python -m mexc_mcp.server --mode public --transport http --port 8000

  # Test with MCP Inspector (after starting the HTTP server above):
  npx @modelcontextprotocol/inspector http://localhost:8000/mcp
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
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type. stdio (default) for subprocess/Claude Desktop; http for remote deployments.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind host for HTTP transport. Default: 0.0.0.0.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Listen port for HTTP transport. Default: 8000.",
    )
    args = parser.parse_args()

    log = logger.bind(mode=args.mode.value, transport=args.transport)

    if args.transport == "http" and args.mode != ServerMode.PUBLIC:
        log.warning(
            "HTTP transport is intended for public mode. "
            "Authenticated tools over HTTP require managed mode with OAuth."
        )

    log.info("starting mexc-mcp server")
    mcp = build_server(args.mode)

    if args.transport == "http":
        log.info("MCP endpoint ready", url=f"http://{args.host}:{args.port}/mcp")
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
