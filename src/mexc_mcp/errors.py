"""Custom exception hierarchy for mexc-mcp.

MEXCAPIError — base for all MEXC API errors; carries HTTP status, error code, and message.
RateLimitError — raised on HTTP 429; signals the caller to back off.
AuthError — raised on signature validation failures or missing/invalid API keys.

Tools catch these exceptions and return user-friendly MCP error content rather
than letting them propagate and crash the MCP session.
"""


class MEXCAPIError(Exception):
    """Raised when MEXC returns a non-success HTTP response."""

    def __init__(self, status: int, code: int | None, message: str) -> None:
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"MEXC API error {status} (code={code}): {message}")


class RateLimitError(MEXCAPIError):
    """Raised on HTTP 429. Caller should back off before retrying."""


class AuthError(MEXCAPIError):
    """Raised on HTTP 401/403 or HMAC signature validation failures."""
