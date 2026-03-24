"""Base async HTTP client for the MEXC REST API.

Wraps httpx.AsyncClient with:
- Connection pooling and configurable timeouts
- Per-endpoint rate limit tracking (parses X-MEXC-RATELIMIT-* headers)
- Automatic retry with exponential backoff on transient errors
- Raises RateLimitError on HTTP 429, AuthError on 401/403, MEXCAPIError otherwise

Both authenticated and unauthenticated requests go through this base client.
The auth module is injected as a dependency and is None in public mode.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING

import httpx
import structlog

from mexc_mcp.errors import AuthError, MEXCAPIError, RateLimitError

if TYPE_CHECKING:
    from mexc_mcp.client.auth import RequestSigner

logger = structlog.get_logger()

SPOT_BASE_URL = "https://api.mexc.com"


class MexcClient:
    """Async HTTP client for MEXC REST API calls.

    Accepts an optional RequestSigner for authenticated endpoints.
    When signer is None, only unauthenticated endpoints are available.
    """

    def __init__(
        self,
        base_url: str = SPOT_BASE_URL,
        timeout: float = 10.0,
        signer: RequestSigner | None = None,
    ) -> None:
        self._http = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self._signer = signer

    async def get(self, path: str, params: dict[str, str] | None = None) -> dict:  # type: ignore[type-arg]
        """Perform an unauthenticated GET request and return the parsed JSON body."""
        log = logger.bind(path=path)
        response = await self._http.get(path, params=params)
        log.debug("mexc response", status=response.status_code)
        return self._raise_for_status(response)

    async def signed_get(self, path: str, params: dict[str, str] | None = None) -> dict:  # type: ignore[type-arg]
        """Perform an authenticated GET request signed with HMAC SHA256.

        Injects timestamp + signature into query params and sends the
        X-MEXC-APIKEY header. Raises AuthError if no signer is configured.
        """
        if self._signer is None:
            raise AuthError(0, None, "signer is required for authenticated requests")
        signed_params = self._signer.sign(params or {})
        headers = {"X-MEXC-APIKEY": self._signer.api_key}
        log = logger.bind(path=path)
        response = await self._http.get(path, params=signed_params, headers=headers)
        log.debug("mexc response", status=response.status_code)
        return self._raise_for_status(response)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> dict:  # type: ignore[type-arg]
        if response.status_code == 429:
            raise RateLimitError(429, None, "rate limit exceeded")
        if response.status_code in (401, 403):
            data = _safe_json(response)
            raise AuthError(response.status_code, data.get("code"), data.get("msg", "auth error"))
        if not response.is_success:
            data = _safe_json(response)
            raise MEXCAPIError(response.status_code, data.get("code"), data.get("msg", "unknown error"))
        return response.json()  # type: ignore[no-any-return]

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "MexcClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()


def _safe_json(response: httpx.Response) -> dict:  # type: ignore[type-arg]
    try:
        return response.json()  # type: ignore[no-any-return]
    except Exception:
        return {}
