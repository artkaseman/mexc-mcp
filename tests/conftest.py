"""Shared test fixtures and configuration for the mexc-mcp test suite.

Provides:
- mexc_mock: respx router scoped to the MEXC base URL for unit tests
- btcusdt_ticker_raw: real MEXC GET /api/v3/ticker/24hr response payload
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
    """Real response payload from GET /api/v3/ticker/24hr?symbol=BTCUSDT.

    Captured 2026-03-23. Use as the authoritative fixture for Ticker model
    and get_ticker tool tests.
    """
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
