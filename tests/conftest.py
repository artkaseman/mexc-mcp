"""Shared test fixtures and configuration for the mexc-mcp test suite.

Provides:
- mexc_mock: respx router scoped to the MEXC base URL for unit tests
- Common test symbols and sample API response payloads
- Mode-specific server fixture stubs for integration tests
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
