"""Application configuration via pydantic-settings.

Loads all settings from environment variables (with .env file fallback).
Performs mode-aware validation: API keys are required in local/managed mode
and optional (ignored) in public mode. Fails fast on startup if required
credentials are absent.

Key settings:
- MEXC_API_KEY / MEXC_SECRET_KEY — MEXC exchange credentials
- MEXC_BASE_URL — override the spot API base URL
- SERVER_MODE — public | local | managed
- MEXC_ENABLE_TRADING — must be 'true' to register trading tools in local mode
- MEXC_ENABLE_WITHDRAWALS — must be 'true' to register withdrawal tools in local mode
"""
