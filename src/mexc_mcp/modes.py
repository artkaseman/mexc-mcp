"""Server deployment modes and tool registration logic.

Defines the ServerMode enum (public, local, managed) and the function that
registers the appropriate tool groups with the FastMCP app for each mode.

This module is the security boundary: authenticated tools are never registered
in public mode — they cannot be discovered or called by a connected LLM client.
"""
