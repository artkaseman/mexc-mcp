"""Unit tests for server mode and tool registration logic.

Tests:
- Public mode registers only PUBLIC_TOOLS
- Local mode registers all tool groups
- Local mode without MEXC_ENABLE_TRADING omits trading tools
- Local mode without MEXC_ENABLE_WITHDRAWALS omits wallet tools
- Invalid mode string raises a clear error at startup
"""
