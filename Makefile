.PHONY: install dev test test-cov lint lint-fix clean run-example

# Default python interpreter
PYTHON ?= python

# ── Installation ────────────────────────────────────────────────────────────

install:
	pip install .

dev:
	pip install -e ".[dev]"

# ── Testing ─────────────────────────────────────────────────────────────────

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v \
		--cov=genesis_pantheon \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml

# ── Linting ──────────────────────────────────────────────────────────────────

lint:
	ruff check genesis_pantheon/ tests/

lint-fix:
	ruff check --fix genesis_pantheon/ tests/

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf htmlcov dist build *.egg-info
	rm -f coverage.xml .coverage

# ── Examples ─────────────────────────────────────────────────────────────────

run-example:
	$(PYTHON) examples/01_hello_world/main.py
