.PHONY: install test test-public test-integration test-all lint format typecheck clean

install:
	uv sync

# Unit tests only — no network, no API keys
test:
	uv run pytest tests/unit -v

# Public integration tests — network required, no API keys
test-public:
	uv run pytest tests/integration/test_public.py -v

# Authenticated integration tests — requires MEXC_API_KEY and MEXC_SECRET_KEY
test-integration:
	uv run pytest tests/integration -v -m "not public_only"

# All tests
test-all:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
