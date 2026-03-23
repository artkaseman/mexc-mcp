"""MEXC API request signing.

Handles HMAC SHA256 signature generation over query strings/request bodies,
timestamp injection, and the X-MEXC-APIKEY header. This module is the single
source of signing logic — no other module should construct signatures.

The auth module never logs key values. It may log the first 4 characters of
the API key prefix to assist debugging without leaking credentials.
"""
