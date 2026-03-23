# CLAUDE.md — Project Instructions

## Project Overview

MCP (Model Context Protocol) server for the MEXC cryptocurrency exchange API. Built with FastMCP, designed to be consumed by Claude Desktop, Claude Code, or any MCP-compatible client.

The server operates in **multiple deployment modes** with distinct trust boundaries:

- **`public`** — Market data tools only. No API keys required. Hostable as a remote service anyone can connect to. Zero trust required — the server never touches user credentials.
- **`local`** — Full tool suite including account queries, trading, and wallet operations. Runs as a local subprocess on the user's machine. API keys stay local, loaded from `.env`. The user trusts only their own process.
- **`managed`** *(future)* — B2B mode. Server holds customer keys server-side (encrypted via secrets manager). Customers authenticate to the MCP server via OAuth. The exchange keys never leave the server.

This split exists because MCP servers are **tool executors, not proxies**. The server must have access to any credentials it needs — there's no mechanism in the protocol for the client to sign requests on the server's behalf. The trust boundary is architectural: if the server needs your keys, it must be trusted. If it doesn't need your keys, it doesn't need to be trusted.

## Conventions

- Python 3.11+, managed by `uv`
- Use `structlog` for all logging (never `print()` in library code — stdout is the MCP protocol stream in stdio transport)
- Use `pydantic` for all data models and API response validation
- Type hints on all function signatures
- Docstrings on all public functions (tools use docstrings for LLM-facing descriptions)
- Tests go in `tests/`, mirroring `src/` structure
- Environment variables for all secrets — never hardcode API keys
- HMAC SHA256 signing logic lives exclusively in the client auth module

## Architecture

```
src/mexc_mcp/
├── server.py              — FastMCP server entry point, mode selection, tool registration
├── modes.py               — ServerMode enum, mode-specific tool registry logic
├── client/
│   ├── __init__.py
│   ├── auth.py            — HMAC SHA256 request signing, timestamp management
│   ├── base.py            — Async HTTP client (httpx), rate limit tracking, retry logic
│   ├── spot.py            — Spot API v3 methods (market data, trading, account)
│   ├── futures.py         — Futures API v1 methods (contracts, positions, orders)
│   └── wallet.py          — Wallet endpoints (deposits, withdrawals, transfers)
├── models/
│   ├── __init__.py
│   ├── common.py          — Shared types (Symbol, OrderSide, OrderType, TimeInForce)
│   ├── market.py          — Market data models (Ticker, OrderBook, Kline, Trade)
│   ├── account.py         — Account models (Balance, Order, TradeHistory)
│   ├── futures.py         — Futures models (Position, FundingRate, Contract)
│   └── wallet.py          — Wallet models (DepositRecord, WithdrawRecord, Transfer)
├── tools/
│   ├── __init__.py        — Tool registry: exports tools grouped by mode capability
│   ├── market.py          — MCP tools: get_ticker, get_orderbook, get_klines, etc.
│   ├── trading.py         — MCP tools: place_order, cancel_order, get_open_orders, etc.
│   ├── account.py         — MCP tools: get_balances, get_trade_history, etc.
│   ├── futures.py         — MCP tools: futures positions, orders, funding rates, etc.
│   └── wallet.py          — MCP tools: deposit/withdraw status, internal transfers, etc.
├── config.py              — Settings via pydantic-settings, mode-aware validation
└── errors.py              — Custom exceptions (MEXCAPIError, RateLimitError, AuthError)
tests/
├── unit/
│   ├── test_auth.py       — Signature generation, timestamp handling
│   ├── test_models.py     — Pydantic model validation and edge cases
│   ├── test_modes.py      — Tool registration per mode, mode validation
│   └── test_tools.py      — Tool input/output contracts with mocked client
├── integration/
│   ├── test_public.py     — Public market data tools (no API key needed)
│   ├── test_client.py     — Authenticated API calls against MEXC (needs API key)
│   └── test_server.py     — MCP protocol round-trip via MCP Inspector
└── conftest.py            — Shared fixtures, mock client factory
```

### Deployment modes and trust boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│  PUBLIC MODE                                                    │
│                                                                 │
│  User's machine              Remote server (yours)              │
│  ┌──────────────┐            ┌──────────────────────┐           │
│  │ Claude       │── HTTP ──→ │ MCP Server (public)   │          │
│  │ Desktop      │            │ market tools only     │── → MEXC │
│  └──────────────┘            │ NO keys, NO auth      │  public  │
│                              └──────────────────────┘  endpoints│
│  Trust: none required. Server sees no credentials.              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  LOCAL MODE                                                     │
│                                                                 │
│  User's machine (everything stays here)                         │
│  ┌──────────────┐    stdio    ┌──────────────────────┐          │
│  │ Claude       │────────────→│ MCP Server (local)   │          │
│  │ Desktop      │             │ all tools            │── → MEXC │
│  └──────────────┘             │ keys from .env       │  authed  │
│                               └──────────────────────┘ endpoints│
│  Trust: user trusts their own machine. Keys never leave.        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  MANAGED MODE (future — B2B)                                    │
│                                                                 │
│  Customer's client            Your infrastructure               │
│  ┌──────────────┐            ┌──────────────────────┐           │
│  │ Customer's   │── OAuth ──→│ MCP Server (managed) │           │
│  │ LLM client   │            │ all tools            │── → MEXC  │
│  └──────────────┘            │ keys from Vault/     │  authed   │
│                              │ secrets manager      │ endpoints │
│                              └──────────────────────┘           │
│  Trust: customer trusts you (contractual, encrypted at rest).   │
│  Exchange keys held server-side, never exposed to client.       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  HYBRID — recommended for personal use                          │
│                                                                 │
│  claude_desktop_config.json registers BOTH servers:             │
│    "mexc-market"   → remote public server (HTTP)                │
│    "mexc-account"  → local authenticated server (stdio)         │
│                                                                 │
│  Claude sees tools from both. Market data is remote.            │
│  Account operations stay local. Keys never leave the machine.   │
└─────────────────────────────────────────────────────────────────┘
```

### Layer responsibilities

**`server.py`** — FastMCP server setup. Reads `--mode` flag (defaults to `local`). Registers only the tools appropriate for the selected mode. Configures transport: stdio for local mode, streamable HTTP for public/managed. This file should be short — just wiring.

**`modes.py`** — Defines `ServerMode` enum (`public`, `local`, `managed`) and the logic for which tool groups register in each mode. Public mode registers only `tools/market.py`. Local mode registers everything. Managed mode registers everything plus audit logging middleware. This is the **security boundary** — tool registration is the enforcement point.

**`client/`** — Standalone async MEXC API client. Zero MCP awareness. Uses `httpx.AsyncClient` for HTTP, handles auth signing, rate limit headers, and retry with exponential backoff. Each submodule maps 1:1 to a MEXC API documentation section. This layer is independently importable and testable — it should work without FastMCP installed. In public mode, the auth module is never instantiated.

**`models/`** — Pydantic v2 models for all API request parameters and response payloads. Models handle MEXC's inconsistent casing and field naming via `model_config` aliases. All numeric fields from the API (which arrive as strings) use custom validators to parse to `Decimal` for financial precision.

**`tools/`** — MCP tool definitions. Each tool is a thin function that validates inputs via Pydantic, calls the appropriate client method, and returns structured data. Tool docstrings are the LLM-facing descriptions — write them as clear, concise instructions an LLM can understand. The `__init__.py` exports tool groups (`PUBLIC_TOOLS`, `AUTHENTICATED_TOOLS`, `TRADING_TOOLS`, `WALLET_TOOLS`) so `modes.py` can selectively register them.

**`config.py`** — Single source for all configuration. Uses `pydantic-settings` to load from environment variables with sensible defaults. **Mode-aware validation**: in public mode, API keys are not required. In local/managed mode, `MEXC_API_KEY` and `MEXC_SECRET_KEY` are required and the server fails fast on startup if missing. Optional: `MEXC_BASE_URL` (defaults to `https://api.mexc.com`), rate limit tuning, timeout values.

**`errors.py`** — Typed exception hierarchy. `MEXCAPIError` wraps any non-200 response with code and message. `RateLimitError` signals 429s for backoff handling. `AuthError` catches signature/key failures. Tools should catch client exceptions and return user-friendly error content rather than crashing the MCP session.

### Key design decisions

1. **Mode-based tool registration is the security boundary.** Authenticated tools don't exist in public mode — they're never registered, not just disabled. An LLM connected to the public server cannot call `get_balances` because the tool literally isn't advertised in the schema. This is defense at the protocol layer, not just a config flag.

2. **FastMCP over low-level SDK** — FastMCP auto-generates tool schemas from type hints and docstrings, reducing boilerplate. Use `@mcp.tool()` decorators in the tools modules, not in server.py.

3. **Async throughout** — MEXC API calls are I/O-bound. The client uses `httpx.AsyncClient` with connection pooling. Tools are async functions.

4. **No WebSocket in v1** — Start with REST polling only. WebSocket streaming (for live orderbook/trades) is a v2 concern. Don't over-engineer the transport layer yet.

5. **Financial precision** — All price/quantity fields use `Decimal`, never `float`. The models enforce this on deserialization.

6. **Rate limit awareness** — The client tracks rate limit headers from MEXC responses (500 requests per 10 seconds per endpoint). Expose remaining capacity as a resource or in tool metadata so the LLM can pace itself. On 429, raise `RateLimitError` — don't silently retry forever.

7. **Tool granularity** — Prefer focused tools (`get_ticker`, `get_orderbook`) over mega-tools (`get_market_data`). LLMs compose small tools better than they navigate complex parameter spaces.

8. **Read-only by default in local mode** — Even with keys present, trading tools require explicit opt-in via `MEXC_ENABLE_TRADING=true`. Withdrawal tools require a separate `MEXC_ENABLE_WITHDRAWALS=true`. Two-tier escalation.

9. **No sandbox available** — MEXC does not offer a test environment. Integration tests hit the live API. Use small quantities on real pairs and clean up after tests. Mark integration tests so they can be skipped in CI.

## MEXC API reference

- Spot v3 docs: https://mexcdevelop.github.io/apidocs/spot_v3_en/
- Futures v1 docs: https://www.mexc.com/api-docs/futures/
- Base URL (spot): `https://api.mexc.com`
- Base URL (futures): `https://contract.mexc.com` (some endpoints use `https://api.mexc.com/api/v1/contract/`)
- Auth: HMAC SHA256 signature over query string, sent via `signature` parameter
- API key header: `X-MEXC-APIKEY`
- Rate limits: 500 per 10 seconds per endpoint, split by IP (public) and UID (authenticated)
- No sandbox/test environment — all API calls hit live

## Dependencies

Core: `fastmcp`, `httpx`, `pydantic`, `pydantic-settings`, `structlog`
Dev: `pytest`, `pytest-asyncio`, `respx` (for httpx mocking), `ruff`, `mypy`

## Running

```bash
# Install dependencies
uv sync

# --- PUBLIC MODE (no API keys needed, hostable) ---

# Run public MCP server locally for testing (stdio)
uv run python -m mexc_mcp.server --mode public

# Run public MCP server for remote access (HTTP)
uv run python -m mexc_mcp.server --mode public --transport http --port 8000

# --- LOCAL MODE (needs MEXC_API_KEY and MEXC_SECRET_KEY in .env) ---

# Run local MCP server (stdio, for Claude Desktop / Claude Code)
uv run python -m mexc_mcp.server --mode local

# Run with trading enabled
MEXC_ENABLE_TRADING=true uv run python -m mexc_mcp.server --mode local

# --- TESTS ---

# Unit tests (no API key needed, no network)
make test

# Integration tests — public endpoints only
make test-public

# Integration tests — authenticated (needs API keys in .env)
make test-integration

# All tests
make test-all

# Lint, format, typecheck
make lint
make format
make typecheck
```

## Claude Desktop configuration

**Hybrid setup (recommended):** remote public server for market data, local server for authenticated operations. API keys never leave your machine.

```json
{
  "mcpServers": {
    "mexc-market": {
      "type": "url",
      "url": "https://your-public-server.example.com/mcp"
    },
    "mexc-account": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mexc-mcp", "python", "-m", "mexc_mcp.server", "--mode", "local"],
      "env": {
        "MEXC_ENABLE_TRADING": "false"
      }
    }
  }
}
```

Note: `mexc-account` does NOT have API keys in the config. Keys are loaded from the project's `.env` file by `pydantic-settings`. The `--directory` flag ensures `uv` runs from the project root where `.env` lives.

**Local-only setup (simpler, all tools in one server):**

```json
{
  "mcpServers": {
    "mexc": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mexc-mcp", "python", "-m", "mexc_mcp.server", "--mode", "local"]
    }
  }
}
```

**Public-only setup (no auth needed, anyone can use):**

```json
{
  "mcpServers": {
    "mexc-market": {
      "type": "url",
      "url": "https://your-public-server.example.com/mcp"
    }
  }
}
```

## Credential management

API keys are loaded in this priority order (first found wins):

1. Environment variables (`MEXC_API_KEY`, `MEXC_SECRET_KEY`)
2. `.env` file in project root (loaded by `pydantic-settings`)
3. *(future, managed mode)* AWS Secrets Manager / HashiCorp Vault

**Rules:**
- `.env` is gitignored — enforced in `.gitignore` at project creation
- Keys never appear in `claude_desktop_config.json` — use `.env` or shell exports
- The auth module never logs key values — only whether a key was found and its prefix (first 4 chars) for debugging
- Public mode skips credential loading entirely — no validation, no warnings about missing keys
- Local mode fails fast on startup if keys are missing — no silent fallback to public mode

## Safety guardrails

**Mode-level enforcement:**
- Public mode: authenticated tools are never registered. The LLM cannot discover or call them.
- Local mode: trading tools disabled unless `MEXC_ENABLE_TRADING=true`. Wallet/withdrawal tools disabled unless `MEXC_ENABLE_WITHDRAWALS=true`. Two separate flags, two separate escalation decisions.
- Managed mode *(future)*: all operations audit-logged with customer ID, tool name, parameters, and result status.

**Operational:**
- All trading tool calls are logged with full parameters via structlog before execution
- The server never logs or exposes API secrets — the auth module handles signing internally
- Tool error responses include the MEXC error code and message but never leak signing details
- Rate limit state is tracked per-endpoint and exposed to the LLM via tool metadata

**MEXC API key permissions (user responsibility, document in README):**
- Recommend users create a dedicated API key for MCP with minimal permissions
- Read-only key for account queries (disable trading/withdrawal on MEXC side)
- Separate key with trading enabled only if `MEXC_ENABLE_TRADING` is used
- IP restriction on MEXC API key to localhost / known IPs
- 90-day key rotation via MEXC's renewal feature

## Roadmap

- **v0.1** — Public mode: market data tools (ticker, orderbook, klines, exchange info). Hostable. Portfolio piece.
- **v0.2** — Local mode: account queries (balances, trade history, open orders). Keys from `.env`.
- **v0.3** — Local mode: spot trading tools (place/cancel orders) with safety flags.
- **v0.4** — Futures tools (positions, funding rates, contract info).
- **v1.0** — Stable public + local modes. Published to PyPI as `mexc-mcp`. README with setup guide.
- **v1.x** — WebSocket support for live data. MCP resources for streaming market state.
- **v2.0** — Managed mode with OAuth, secrets manager integration, multi-tenant customer isolation.