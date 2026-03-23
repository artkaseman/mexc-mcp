"""Integration tests for full MCP protocol round-trips.

Starts a local MCP server subprocess and communicates via the MCP protocol
(using the MCP Python SDK or MCP Inspector) to verify end-to-end behavior.

Tests:
- Public mode server advertises only market data tools
- Local mode server (with test API keys) advertises account tools
- Tool call returns valid structured response
- Server handles malformed tool input gracefully
"""
