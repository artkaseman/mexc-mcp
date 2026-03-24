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

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mexc_api_key: str = ""
    mexc_secret_key: str = ""
    mexc_base_url: str = "https://api.mexc.com"
    mexc_enable_trading: bool = False
    mexc_enable_withdrawals: bool = False


def get_settings() -> Settings:
    """Return a Settings instance populated from the environment."""
    return Settings()
