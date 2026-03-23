"""Unit tests for MCP tool input/output contracts.

Uses a mock client (injected via conftest fixture) to test tools
without any network calls.

Tests:
- Tools pass validated parameters to the client method
- Client errors are caught and returned as user-friendly MCP content
- Tool return values match expected structure
- Invalid inputs raise appropriate validation errors before hitting the client
"""
