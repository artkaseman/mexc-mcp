"""Base async HTTP client for the MEXC REST API.

Wraps httpx.AsyncClient with:
- Connection pooling and configurable timeouts
- Per-endpoint rate limit tracking (parses X-MEXC-RATELIMIT-* headers)
- Automatic retry with exponential backoff on transient errors
- Raises RateLimitError on HTTP 429, AuthError on 401/403, MEXCAPIError otherwise

Both authenticated and unauthenticated requests go through this base client.
The auth module is injected as a dependency and is None in public mode.
"""
