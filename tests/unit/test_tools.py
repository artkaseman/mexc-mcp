"""Unit tests for MCP tool input/output contracts.

Uses respx to intercept httpx requests — no real network calls.
"""

import httpx

from mexc_mcp.tools.market import get_ticker, ping_mexc


# ---------------------------------------------------------------------------
# ping_mexc
# ---------------------------------------------------------------------------


async def test_ping_mexc_success(mexc_mock):
    """ping_mexc returns a reachability message on HTTP 200."""
    mexc_mock.get("/api/v3/ping").mock(return_value=httpx.Response(200, json={}))

    result = await ping_mexc()

    assert "reachable" in result.lower()


async def test_ping_mexc_server_error(mexc_mock):
    """ping_mexc surfaces the MEXC error message on HTTP 500."""
    mexc_mock.get("/api/v3/ping").mock(
        return_value=httpx.Response(500, json={"code": -1, "msg": "internal server error"})
    )

    result = await ping_mexc()

    assert "error" in result.lower()


async def test_ping_mexc_rate_limited(mexc_mock):
    """ping_mexc surfaces a rate-limit error on HTTP 429."""
    mexc_mock.get("/api/v3/ping").mock(return_value=httpx.Response(429))

    result = await ping_mexc()

    assert "error" in result.lower()


# ---------------------------------------------------------------------------
# get_ticker
# ---------------------------------------------------------------------------


async def test_get_ticker_success(mexc_mock, btcusdt_ticker_raw):
    """get_ticker returns a dict with expected keys on HTTP 200."""
    mexc_mock.get("/api/v3/ticker/24hr").mock(
        return_value=httpx.Response(200, json=btcusdt_ticker_raw)
    )

    result = await get_ticker("BTCUSDT")

    assert result["symbol"] == "BTCUSDT"
    assert result["last_price"] == "70996.79"
    assert result["high_price"] == "71810"
    assert result["volume"] == "15315.74637732"
    assert result["count"] is None


async def test_get_ticker_uppercases_symbol(mexc_mock, btcusdt_ticker_raw):
    """get_ticker normalises lowercase symbol input to uppercase."""
    route = mexc_mock.get("/api/v3/ticker/24hr").mock(
        return_value=httpx.Response(200, json=btcusdt_ticker_raw)
    )

    await get_ticker("btcusdt")

    assert route.called
    called_url = str(route.calls[0].request.url)
    assert "BTCUSDT" in called_url


async def test_get_ticker_unknown_symbol(mexc_mock):
    """get_ticker returns an error dict when MEXC rejects the symbol."""
    mexc_mock.get("/api/v3/ticker/24hr").mock(
        return_value=httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})
    )

    result = await get_ticker("NOTREAL")

    assert "error" in result
    assert result["code"] == -1121


async def test_get_ticker_decimal_fields_serialized_as_strings(mexc_mock, btcusdt_ticker_raw):
    """model_dump(mode='json') serializes Decimal fields as strings, not floats."""
    mexc_mock.get("/api/v3/ticker/24hr").mock(
        return_value=httpx.Response(200, json=btcusdt_ticker_raw)
    )

    result = await get_ticker("BTCUSDT")

    # All price/volume fields should be strings (Decimal → str via mode='json')
    for field in ("last_price", "high_price", "low_price", "volume", "quote_volume"):
        assert isinstance(result[field], str), f"{field} should be str, got {type(result[field])}"
