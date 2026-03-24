"""MEXC API request signing.

Handles HMAC SHA256 signature generation over query strings/request bodies,
timestamp injection, and the X-MEXC-APIKEY header. This module is the single
source of signing logic — no other module should construct signatures.

The auth module never logs key values. It may log the first 4 characters of
the API key prefix to assist debugging without leaking credentials.

Signing protocol (MEXC Spot v3):
  - totalParams = query_string + body  (concatenated without any separator
    for mixed requests; body only or query string only for pure cases)
  - signature   = HMAC-SHA256(secret_key, totalParams).hexdigest()  [lowercase]
  - Header      : X-MEXC-APIKEY: <api_key>
  - Parameter   : signature=<hex>

Reference: https://mexcdevelop.github.io/apidocs/spot_v3_en/#signed-trade-and-user-data-request
"""

import hashlib
import hmac
import time
from urllib.parse import urlencode

import structlog

logger = structlog.get_logger()


class RequestSigner:
    """HMAC SHA256 signer for authenticated MEXC API requests.

    Injects timestamp and signature into parameter dicts so the base HTTP
    client can attach them as query-string parameters.  The secret key is
    stored only in memory and is never exposed or logged.

    Usage::

        signer = RequestSigner(api_key="...", secret_key="...")

        # Add timestamp + signature to a params dict (returns a new dict)
        signed = signer.sign({"symbol": "BTCUSDT", "side": "BUY", ...})

        # Low-level: sign a pre-built totalParams string directly
        hex_sig = signer.sign_query_string("symbol=BTCUSDT&timestamp=...")
    """

    def __init__(self, api_key: str, secret_key: str) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        if not secret_key:
            raise ValueError("secret_key must not be empty")
        self._api_key = api_key
        # Pre-encode once; re-used on every sign call.
        self._secret_bytes = secret_key.encode()
        logger.debug("RequestSigner initialised", api_key_prefix=api_key[:4])

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def api_key(self) -> str:
        """Public API key — safe to include in the X-MEXC-APIKEY header."""
        return self._api_key

    @staticmethod
    def current_timestamp() -> int:
        """Current UTC time in milliseconds (as required by MEXC)."""
        return int(time.time() * 1000)

    def sign_query_string(self, total_params: str) -> str:
        """Return the HMAC SHA256 hex digest of *total_params*.

        *total_params* is the verbatim string to sign as defined by MEXC:

        - Query-string-only requests: the URL-encoded query string.
        - Body-only requests: the URL-encoded request body.
        - Mixed requests: query_string + body concatenated with **no**
          separator (not even ``&``).

        The result is always lowercase, as required by MEXC.
        """
        return hmac.new(
            self._secret_bytes,
            total_params.encode(),
            hashlib.sha256,
        ).hexdigest()

    def sign(
        self,
        params: dict[str, str],
        *,
        timestamp: int | None = None,
    ) -> dict[str, str]:
        """Return a **new** params dict with *timestamp* and *signature* appended.

        The caller's dict is never modified.  Timestamp is appended after all
        provided params (matching the ordering shown in the MEXC docs), then
        the signature is computed over the URL-encoded string and appended last.

        Args:
            params:    Request parameters without timestamp or signature.
            timestamp: Milliseconds since epoch (UTC).  Defaults to now.

        Returns:
            New dict: original params + ``timestamp`` + ``signature``.
        """
        signed: dict[str, str] = dict(params)
        signed["timestamp"] = str(
            timestamp if timestamp is not None else self.current_timestamp()
        )
        total_params = urlencode(signed)
        signed["signature"] = self.sign_query_string(total_params)
        return signed
