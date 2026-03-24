"""Shared test fixtures and configuration for the mexc-mcp test suite.

Provides:
- mexc_mock: respx router scoped to the MEXC base URL for unit tests
- Real API response fixtures for each implemented endpoint (captured 2026-03-23)
"""

import pytest
import respx

MEXC_BASE_URL = "https://api.mexc.com"


@pytest.fixture
def mexc_mock():
    """respx mock router scoped to https://api.mexc.com.

    Intercepts all httpx requests to the MEXC base URL within the test.
    Any unmocked URL will raise a respx.NetworkError.
    """
    with respx.mock(base_url=MEXC_BASE_URL, assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def btcusdt_ticker_raw() -> dict:  # type: ignore[type-arg]
    """Real response payload from GET /api/v3/ticker/24hr?symbol=BTCUSDT."""
    return {
        "symbol": "BTCUSDT",
        "priceChange": "3090.1",
        "priceChangePercent": "0.0455",
        "prevClosePrice": "67906.69",
        "lastPrice": "70996.79",
        "bidPrice": "71005.16",
        "bidQty": "1.44656033",
        "askPrice": "71005.17",
        "askQty": "0.00151758",
        "openPrice": "67906.69",
        "highPrice": "71810",
        "lowPrice": "67445.33",
        "volume": "15315.74637732",
        "quoteVolume": "1068547727.91",
        "openTime": 1774310542044,
        "closeTime": 1774310553112,
        "count": None,
    }


@pytest.fixture
def btcusdt_depth_raw() -> dict:  # type: ignore[type-arg]
    """Real response payload from GET /api/v3/depth?symbol=BTCUSDT&limit=5."""
    return {
        "lastUpdateId": 66261959114,
        "bids": [
            ["70808.49", "0.20819013"],
            ["70808.48", "0.00127783"],
            ["70808.09", "0.00128884"],
            ["70807.97", "0.08455425"],
            ["70807.45", "0.00143628"],
        ],
        "asks": [
            ["70808.50", "0.63007237"],
            ["70809.07", "0.01419554"],
            ["70810.06", "0.01419554"],
            ["70810.42", "0.49062693"],
            ["70810.71", "0.01419554"],
        ],
        "timestamp": 1774311155172,
    }


@pytest.fixture
def btcusdt_klines_raw() -> list:  # type: ignore[type-arg]
    """Real response payload from GET /api/v3/klines?symbol=BTCUSDT&interval=60m&limit=3.

    Each element is [openTime, open, high, low, close, volume, closeTime, quoteVolume].
    """
    return [
        [1774303200000, "70847.26", "70896.52", "70525.2", "70791.25", "201.17259457", 1774306800000, "14217200.73"],
        [1774306800000, "70791.25", "70990", "70409.65", "70902.7", "254.63750736", 1774310400000, "18004928.66"],
        [1774310400000, "70902.7", "71098.64", "70783.03", "70788.31", "157.63932862", 1774314000000, "11184746.59"],
    ]


@pytest.fixture
def btcusdt_open_orders_raw() -> list:  # type: ignore[type-arg]
    """Realistic response from GET /api/v3/openOrders?symbol=BTCUSDT."""
    return [
        {
            "symbol": "BTCUSDT",
            "orderId": "C02__474250929059741696",
            "orderListId": -1,
            "clientOrderId": None,
            "price": "50000.00",
            "origQty": "0.001",
            "executedQty": "0.00000000",
            "cummulativeQuoteQty": "0.00000000",
            "status": "NEW",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "BUY",
            "stopPrice": "0.00000000",
            "icebergQty": "0.00000000",
            "time": 1714001234000,
            "updateTime": 1714001234000,
            "isWorking": True,
            "origQuoteOrderQty": "50.00",
        }
    ]


@pytest.fixture
def btcusdt_trade_history_raw() -> list:  # type: ignore[type-arg]
    """Realistic response from GET /api/v3/myTrades?symbol=BTCUSDT."""
    return [
        {
            "symbol": "BTCUSDT",
            "id": "C02__474250929059741697",
            "orderId": "C02__474250929059741698",
            "orderListId": -1,
            "price": "70996.79",
            "qty": "0.001",
            "quoteQty": "70.99679",
            "commission": "0.03549840",
            "commissionAsset": "USDT",
            "time": 1714001234000,
            "isBuyer": True,
            "isMaker": False,
            "isBestMatch": True,
        },
        {
            "symbol": "BTCUSDT",
            "id": "C02__474250929059741699",
            "orderId": "C02__474250929059741700",
            "orderListId": -1,
            "price": "71500.00",
            "qty": "0.002",
            "quoteQty": "143.00",
            "commission": "0.00000200",
            "commissionAsset": "BTC",
            "time": 1714001290000,
            "isBuyer": False,
            "isMaker": True,
            "isBestMatch": True,
        },
    ]


@pytest.fixture
def btcusdt_exchange_info_raw() -> dict:  # type: ignore[type-arg]
    """Real response payload from GET /api/v3/exchangeInfo?symbol=BTCUSDT."""
    return {
        "timezone": "CST",
        "serverTime": 1774311163463,
        "rateLimits": [],
        "exchangeFilters": [],
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "1",
                "baseAsset": "BTC",
                "baseAssetPrecision": 8,
                "quoteAsset": "USDT",
                "quotePrecision": 2,
                "quoteAssetPrecision": 2,
                "baseCommissionPrecision": 8,
                "quoteCommissionPrecision": 2,
                "orderTypes": ["LIMIT", "MARKET", "LIMIT_MAKER"],
                "isSpotTradingAllowed": True,
                "isMarginTradingAllowed": False,
                "quoteAmountPrecision": "1",
                "baseSizePrecision": "0.000001",
                "permissions": ["SPOT"],
                "filters": [
                    {
                        "filterType": "PERCENT_PRICE_BY_SIDE",
                        "bidMultiplierUp": "0.005",
                        "askMultiplierDown": "0.005",
                    }
                ],
                "maxQuoteAmount": "4000000",
                "makerCommission": "0",
                "takerCommission": "0.0005",
                "quoteAmountPrecisionMarket": "1",
                "maxQuoteAmountMarket": "4000000",
                "fullName": "Bitcoin",
                "tradeSideType": 1,
                "contractAddress": "",
                "conceptPlateIds": [50, 5, 39, 12],
                "st": False,
            }
        ],
    }
