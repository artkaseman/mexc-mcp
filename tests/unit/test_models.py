"""Unit tests for Pydantic model validation.

Tests:
- Price/quantity string fields are coerced to Decimal on construction
- Invalid values raise ValidationError with descriptive messages
- Model aliases handle MEXC's inconsistent field casing
- Edge cases: zero quantities, very large prices, missing optional fields
"""
