"""Unit tests for MCP tool input/output contracts.

Uses respx to intercept httpx requests — no real network calls.
"""

import httpx
import pytest

from mexc_mcp.tools.account import get_balances
from mexc_mcp.tools.market import get_exchange_info, get_klines, get_orderbook, get_ticker, ping_mexc


# ---------------------------------------------------------------------------
# ping_mexc
# ---------------------------------------------------------------------------


async def test_ping_mexc_success(mexc_mock):
    mexc_mock.get("/api/v3/ping").mock(return_value=httpx.Response(200, json={}))

    result = await ping_mexc()

    assert "reachable" in result.lower()


async def test_ping_mexc_server_error(mexc_mock):
    mexc_mock.get("/api/v3/ping").mock(
        return_value=httpx.Response(500, json={"code": -1, "msg": "internal server error"})
    )

    result = await ping_mexc()

    assert "error" in result.lower()


async def test_ping_mexc_rate_limited(mexc_mock):
    mexc_mock.get("/api/v3/ping").mock(return_value=httpx.Response(429))

    result = await ping_mexc()

    assert "error" in result.lower()


# ---------------------------------------------------------------------------
# get_ticker
# ---------------------------------------------------------------------------


async def test_get_ticker_success(mexc_mock, btcusdt_ticker_raw):
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
    route = mexc_mock.get("/api/v3/ticker/24hr").mock(
        return_value=httpx.Response(200, json=btcusdt_ticker_raw)
    )

    await get_ticker("btcusdt")

    assert route.called
    assert "BTCUSDT" in str(route.calls[0].request.url)


async def test_get_ticker_unknown_symbol(mexc_mock):
    mexc_mock.get("/api/v3/ticker/24hr").mock(
        return_value=httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})
    )

    result = await get_ticker("NOTREAL")

    assert "error" in result
    assert result["code"] == -1121


async def test_get_ticker_decimal_fields_serialized_as_strings(mexc_mock, btcusdt_ticker_raw):
    mexc_mock.get("/api/v3/ticker/24hr").mock(
        return_value=httpx.Response(200, json=btcusdt_ticker_raw)
    )

    result = await get_ticker("BTCUSDT")

    for field in ("last_price", "high_price", "low_price", "volume", "quote_volume"):
        assert isinstance(result[field], str), f"{field} should be str, got {type(result[field])}"


# ---------------------------------------------------------------------------
# get_orderbook
# ---------------------------------------------------------------------------


async def test_get_orderbook_success(mexc_mock, btcusdt_depth_raw):
    mexc_mock.get("/api/v3/depth").mock(
        return_value=httpx.Response(200, json=btcusdt_depth_raw)
    )

    result = await get_orderbook("BTCUSDT")

    assert result["last_update_id"] == 66261959114
    assert len(result["bids"]) == 5
    assert len(result["asks"]) == 5


async def test_get_orderbook_levels_are_string_pairs(mexc_mock, btcusdt_depth_raw):
    """Decimal bids/asks serialize as [price_str, qty_str] pairs."""
    mexc_mock.get("/api/v3/depth").mock(
        return_value=httpx.Response(200, json=btcusdt_depth_raw)
    )

    result = await get_orderbook("BTCUSDT")

    best_bid = result["bids"][0]
    assert best_bid == ["70808.49", "0.20819013"]
    best_ask = result["asks"][0]
    assert best_ask == ["70808.50", "0.63007237"]


async def test_get_orderbook_passes_limit(mexc_mock, btcusdt_depth_raw):
    route = mexc_mock.get("/api/v3/depth").mock(
        return_value=httpx.Response(200, json=btcusdt_depth_raw)
    )

    await get_orderbook("BTCUSDT", limit=5)

    assert "limit=5" in str(route.calls[0].request.url)


async def test_get_orderbook_error(mexc_mock):
    mexc_mock.get("/api/v3/depth").mock(
        return_value=httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})
    )

    result = await get_orderbook("FAKE")

    assert "error" in result


# ---------------------------------------------------------------------------
# get_klines
# ---------------------------------------------------------------------------


async def test_get_klines_success(mexc_mock, btcusdt_klines_raw):
    mexc_mock.get("/api/v3/klines").mock(
        return_value=httpx.Response(200, json=btcusdt_klines_raw)
    )

    result = await get_klines("BTCUSDT", "60m", limit=3)

    assert result["symbol"] == "BTCUSDT"
    assert result["interval"] == "60m"
    assert len(result["klines"]) == 3


async def test_get_klines_candle_fields(mexc_mock, btcusdt_klines_raw):
    mexc_mock.get("/api/v3/klines").mock(
        return_value=httpx.Response(200, json=btcusdt_klines_raw)
    )

    result = await get_klines("BTCUSDT", "60m")
    first = result["klines"][0]

    assert first["open_time"] == 1774303200000
    assert first["open"] == "70847.26"
    assert first["high"] == "70896.52"
    assert first["low"] == "70525.2"
    assert first["close"] == "70791.25"
    assert first["volume"] == "201.17259457"
    assert first["close_time"] == 1774306800000
    assert first["quote_volume"] == "14217200.73"


async def test_get_klines_invalid_interval(mexc_mock):
    mexc_mock.get("/api/v3/klines").mock(
        return_value=httpx.Response(400, json={"code": -1121, "msg": "Invalid interval."})
    )

    result = await get_klines("BTCUSDT", "1h")  # wrong — should be "60m"

    assert "error" in result


async def test_get_klines_passes_params(mexc_mock, btcusdt_klines_raw):
    route = mexc_mock.get("/api/v3/klines").mock(
        return_value=httpx.Response(200, json=btcusdt_klines_raw)
    )

    await get_klines("BTCUSDT", "60m", limit=3)

    url = str(route.calls[0].request.url)
    assert "symbol=BTCUSDT" in url
    assert "interval=60m" in url
    assert "limit=3" in url


# ---------------------------------------------------------------------------
# get_exchange_info
# ---------------------------------------------------------------------------


async def test_get_exchange_info_success(mexc_mock, btcusdt_exchange_info_raw):
    mexc_mock.get("/api/v3/exchangeInfo").mock(
        return_value=httpx.Response(200, json=btcusdt_exchange_info_raw)
    )

    result = await get_exchange_info("BTCUSDT")

    assert result["timezone"] == "CST"
    assert len(result["symbols"]) == 1
    sym = result["symbols"][0]
    assert sym["symbol"] == "BTCUSDT"
    assert sym["base_asset"] == "BTC"
    assert sym["taker_commission"] == "0.0005"


async def test_get_exchange_info_trading_flags(mexc_mock, btcusdt_exchange_info_raw):
    mexc_mock.get("/api/v3/exchangeInfo").mock(
        return_value=httpx.Response(200, json=btcusdt_exchange_info_raw)
    )

    result = await get_exchange_info("BTCUSDT")
    sym = result["symbols"][0]

    assert sym["is_spot_trading_allowed"] is True
    assert sym["is_margin_trading_allowed"] is False


async def test_get_exchange_info_error(mexc_mock):
    mexc_mock.get("/api/v3/exchangeInfo").mock(
        return_value=httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})
    )

    result = await get_exchange_info("FAKE")

    assert "error" in result


# ---------------------------------------------------------------------------
# get_balances
# ---------------------------------------------------------------------------

_ACCOUNT_RAW = {
    "makerCommission": 0,
    "takerCommission": 5,
    "buyerCommission": 0,
    "sellerCommission": 0,
    "canTrade": True,
    "canWithdraw": False,
    "canDeposit": False,
    "updateTime": None,
    "accountType": "SPOT",
    "balances": [
        {"asset": "BTC", "free": "0.5", "locked": "0.1"},
        {"asset": "USDT", "free": "1000.00", "locked": "0.00"},
        {"asset": "ETH", "free": "0.0", "locked": "0.0"},  # zero — should be filtered
    ],
    "permissions": ["SPOT"],
}


@pytest.fixture
def auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject fake API credentials into the environment for tool tests."""
    monkeypatch.setenv("MEXC_API_KEY", "test_api_key_1234")
    monkeypatch.setenv("MEXC_SECRET_KEY", "test_secret_key_5678")


async def test_get_balances_success(mexc_mock, auth_env):
    mexc_mock.get("/api/v3/account").mock(
        return_value=httpx.Response(200, json=_ACCOUNT_RAW)
    )

    result = await get_balances()

    assert result["account_type"] == "SPOT"
    assert result["can_trade"] is True
    assert len(result["balances"]) == 2  # ETH with zero balance filtered out


async def test_get_balances_filters_zero_balances(mexc_mock, auth_env):
    mexc_mock.get("/api/v3/account").mock(
        return_value=httpx.Response(200, json=_ACCOUNT_RAW)
    )

    result = await get_balances()

    assets = {b["asset"] for b in result["balances"]}
    assert "BTC" in assets
    assert "USDT" in assets
    assert "ETH" not in assets  # zero free + zero locked


async def test_get_balances_decimal_fields_are_strings(mexc_mock, auth_env):
    mexc_mock.get("/api/v3/account").mock(
        return_value=httpx.Response(200, json=_ACCOUNT_RAW)
    )

    result = await get_balances()

    btc = next(b for b in result["balances"] if b["asset"] == "BTC")
    assert btc["free"] == "0.5"
    assert btc["locked"] == "0.1"
    assert isinstance(btc["free"], str)
    assert isinstance(btc["locked"], str)


async def test_get_balances_sends_api_key_header(mexc_mock, auth_env):
    route = mexc_mock.get("/api/v3/account").mock(
        return_value=httpx.Response(200, json=_ACCOUNT_RAW)
    )

    await get_balances()

    assert route.called
    assert route.calls[0].request.headers.get("x-mexc-apikey") == "test_api_key_1234"


async def test_get_balances_sends_signature_param(mexc_mock, auth_env):
    route = mexc_mock.get("/api/v3/account").mock(
        return_value=httpx.Response(200, json=_ACCOUNT_RAW)
    )

    await get_balances()

    url = str(route.calls[0].request.url)
    assert "signature=" in url
    assert "timestamp=" in url


async def test_get_balances_auth_error(mexc_mock, auth_env):
    mexc_mock.get("/api/v3/account").mock(
        return_value=httpx.Response(401, json={"code": -2014, "msg": "API-key format invalid."})
    )

    result = await get_balances()

    assert "error" in result


async def test_get_balances_missing_credentials(monkeypatch: pytest.MonkeyPatch):
    """Empty API key raises ValueError caught by the tool — returns error dict."""
    monkeypatch.setenv("MEXC_API_KEY", "")
    monkeypatch.setenv("MEXC_SECRET_KEY", "")

    result = await get_balances()

    assert "error" in result
    assert "authentication" in result["error"].lower()
