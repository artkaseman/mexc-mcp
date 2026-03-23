"""FastMCP server entry point.

Reads the --mode flag (defaults to 'local'), instantiates the FastMCP app,
delegates tool registration to modes.py, and starts the appropriate transport:
- stdio   for local mode (subprocess, Claude Desktop)
- HTTP    for public/managed mode (remote, streamable)

This module is intentionally thin — it is pure wiring. No business logic lives here.
"""
