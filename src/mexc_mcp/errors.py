"""Custom exception hierarchy for mexc-mcp.

MEXCAPIError — base for all MEXC API errors; carries HTTP status, error code, and message.
RateLimitError — raised on HTTP 429; signals the caller to back off.
AuthError — raised on signature validation failures or missing/invalid API keys.

Tools catch these exceptions and return user-friendly MCP error content rather
than letting them propagate and crash the MCP session.
"""
