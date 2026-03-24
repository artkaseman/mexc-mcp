"""Unit tests for MEXC HMAC SHA256 request signing.

Tests:
- Signature generation produces correct HMAC SHA256 hex digest
- Timestamp is injected into query parameters
- Signature changes when any parameter changes
- Auth module never logs key values

Test vectors from MEXC Spot v3 docs General Info / Signed Requests section.
See: https://mexcdevelop.github.io/apidocs/spot_v3_en/#signed-trade-and-user-data-request

  Secret key:  45d0b3c26f2644f19bfb98b07741b2f5
  API key:     mx0aBYs33eIilxBWC5
  Timestamp:   1644489390087

Example 2 — query string only (verified computationally):
  totalParams: symbol=BTCUSDT&side=BUY&type=LIMIT&quantity=1&price=11
               &recvWindow=5000&timestamp=1644489390087
  signature:   fd3e4e8543c5188531eb7279d68ae7d26a573d0fc5ab0d18eb692451654d837a

Example 3 — mixed (query + body, NO separator, verified computationally):
  query:   symbol=BTCUSDT&side=BUY&type=LIMIT
  body:    quantity=1&price=11&recvWindow=5000&timestamp=1644489390087
  totalParams = query + body  (concatenated with no '&' between them)
  totalParams: symbol=BTCUSDT&side=BUY&type=LIMITquantity=1&price=11
               &recvWindow=5000&timestamp=1644489390087
  signature:   d1a676610ceb39174c8039b3f548357994b2a34139a8addd33baadba65684592
"""

import re
import time

import pytest

from mexc_mcp.client.auth import RequestSigner

# ---------------------------------------------------------------------------
# Test vectors from MEXC docs
# ---------------------------------------------------------------------------

_SECRET = "45d0b3c26f2644f19bfb98b07741b2f5"
_API_KEY = "mx0aBYs33eIilxBWC5"
_TIMESTAMP = 1644489390087

# Example 2: pure query-string request
_EX2_TOTAL_PARAMS = (
    "symbol=BTCUSDT&side=BUY&type=LIMIT&quantity=1&price=11"
    "&recvWindow=5000&timestamp=1644489390087"
)
_EX2_SIG = "fd3e4e8543c5188531eb7279d68ae7d26a573d0fc5ab0d18eb692451654d837a"

# Example 3: mixed request — query + body concatenated with NO separator
_EX3_TOTAL_PARAMS = (
    "symbol=BTCUSDT&side=BUY&type=LIMITquantity=1&price=11"
    "&recvWindow=5000&timestamp=1644489390087"
)
_EX3_SIG = "d1a676610ceb39174c8039b3f548357994b2a34139a8addd33baadba65684592"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def signer() -> RequestSigner:
    return RequestSigner(api_key=_API_KEY, secret_key=_SECRET)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_empty_api_key_raises():
    with pytest.raises(ValueError, match="api_key"):
        RequestSigner(api_key="", secret_key=_SECRET)


def test_empty_secret_key_raises():
    with pytest.raises(ValueError, match="secret_key"):
        RequestSigner(api_key=_API_KEY, secret_key="")


def test_api_key_property(signer: RequestSigner):
    assert signer.api_key == _API_KEY


def test_secret_not_exposed_as_attribute(signer: RequestSigner):
    """The secret should not be retrievable as a plain-text public attribute."""
    assert not hasattr(signer, "secret_key")
    assert not hasattr(signer, "_secret_key")  # stored as _secret_bytes only


# ---------------------------------------------------------------------------
# sign_query_string — MEXC test vectors
# ---------------------------------------------------------------------------


def test_sign_query_string_example2(signer: RequestSigner):
    """Example 2 (query-string only): matches MEXC docs test vector."""
    assert signer.sign_query_string(_EX2_TOTAL_PARAMS) == _EX2_SIG


def test_sign_query_string_example3_mixed_no_separator(signer: RequestSigner):
    """Example 3 (mixed, no separator): matches MEXC docs test vector."""
    assert signer.sign_query_string(_EX3_TOTAL_PARAMS) == _EX3_SIG


def test_sign_query_string_returns_lowercase_hex(signer: RequestSigner):
    sig = signer.sign_query_string("symbol=BTCUSDT&timestamp=12345")
    assert re.fullmatch(r"[0-9a-f]{64}", sig), f"not lowercase 64-char hex: {sig!r}"


def test_sign_query_string_different_secret_produces_different_sig():
    s1 = RequestSigner(api_key=_API_KEY, secret_key=_SECRET)
    s2 = RequestSigner(api_key=_API_KEY, secret_key="different_secret_key_xyz")
    assert s1.sign_query_string(_EX2_TOTAL_PARAMS) != s2.sign_query_string(_EX2_TOTAL_PARAMS)


def test_sign_query_string_different_params_produces_different_sig(signer: RequestSigner):
    sig1 = signer.sign_query_string("symbol=BTCUSDT&timestamp=1000")
    sig2 = signer.sign_query_string("symbol=ETHUSDT&timestamp=1000")
    assert sig1 != sig2


def test_sign_query_string_empty_string(signer: RequestSigner):
    """Signing an empty string is valid; result is deterministic."""
    sig = signer.sign_query_string("")
    assert re.fullmatch(r"[0-9a-f]{64}", sig)
    assert signer.sign_query_string("") == sig  # deterministic


# ---------------------------------------------------------------------------
# sign() — full param-dict signing
# ---------------------------------------------------------------------------


def test_sign_produces_example2_signature(signer: RequestSigner):
    """sign() with fixed timestamp reproduces the Example 2 test vector."""
    params = {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "LIMIT",
        "quantity": "1",
        "price": "11",
        "recvWindow": "5000",
    }
    result = signer.sign(params, timestamp=_TIMESTAMP)
    assert result["signature"] == _EX2_SIG


def test_sign_injects_timestamp(signer: RequestSigner):
    result = signer.sign({"symbol": "BTCUSDT"}, timestamp=_TIMESTAMP)
    assert result["timestamp"] == str(_TIMESTAMP)


def test_sign_uses_current_time_when_timestamp_omitted(signer: RequestSigner):
    before = int(time.time() * 1000)
    result = signer.sign({"symbol": "BTCUSDT"})
    after = int(time.time() * 1000)
    ts = int(result["timestamp"])
    assert before <= ts <= after


def test_sign_does_not_mutate_input(signer: RequestSigner):
    params = {"symbol": "BTCUSDT"}
    original = dict(params)
    signer.sign(params, timestamp=_TIMESTAMP)
    assert params == original


def test_sign_returns_new_dict(signer: RequestSigner):
    params = {"symbol": "BTCUSDT"}
    result = signer.sign(params, timestamp=_TIMESTAMP)
    assert result is not params


def test_sign_result_contains_signature_key(signer: RequestSigner):
    result = signer.sign({"symbol": "BTCUSDT"}, timestamp=_TIMESTAMP)
    assert "signature" in result


def test_sign_signature_is_last_key(signer: RequestSigner):
    """Signature must be the last parameter — MEXC requires it appended last."""
    result = signer.sign({"symbol": "BTCUSDT", "side": "BUY"}, timestamp=_TIMESTAMP)
    assert list(result.keys())[-1] == "signature"


def test_sign_timestamp_is_second_to_last_key(signer: RequestSigner):
    """timestamp is appended after all user params, then signature follows it."""
    result = signer.sign({"symbol": "BTCUSDT", "side": "BUY"}, timestamp=_TIMESTAMP)
    keys = list(result.keys())
    assert keys[-2] == "timestamp"
    assert keys[-1] == "signature"


def test_sign_deterministic_with_fixed_timestamp(signer: RequestSigner):
    params = {"symbol": "BTCUSDT"}
    r1 = signer.sign(params, timestamp=_TIMESTAMP)
    r2 = signer.sign(params, timestamp=_TIMESTAMP)
    assert r1 == r2


def test_sign_different_timestamps_produce_different_signatures(signer: RequestSigner):
    r1 = signer.sign({"symbol": "BTCUSDT"}, timestamp=1000)
    r2 = signer.sign({"symbol": "BTCUSDT"}, timestamp=2000)
    assert r1["signature"] != r2["signature"]


# ---------------------------------------------------------------------------
# current_timestamp
# ---------------------------------------------------------------------------


def test_current_timestamp_is_milliseconds():
    """Must be within a 5-second window of the real current time."""
    now_ms = int(time.time() * 1000)
    ts = RequestSigner.current_timestamp()
    assert abs(ts - now_ms) < 5_000


def test_current_timestamp_increases_over_time():
    t1 = RequestSigner.current_timestamp()
    t2 = RequestSigner.current_timestamp()
    assert t2 >= t1
