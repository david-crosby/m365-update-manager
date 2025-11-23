.PHONY: help install test lint format clean check-updates promote

help:
	@echo "M365 Update Manager - Development Commands"
	@echo ""
	@echo "install       Install dependencies with uv"
	@echo "test          Run tests with coverage"
	@echo "lint          Run linter"
	@echo "format        Format code"
	@echo "type-check    Run type checker"
	@echo "clean         Remove build artifacts and cache"
	@echo "check-updates Check for M365 updates (dry-run)"
	@echo "promote       Promote staged updates (dry-run)"
	@echo "setup-hooks   Install pre-commit hooks"

install:
	uv sync --all-extras --dev

test:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run mypy src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf dist/ build/ htmlcov/ .coverage

check-updates:
	uv run python check_updates.py --dry-run --verbose

promote:
	uv run python promote.py --dry-run --verbose

setup-hooks:
	uv run pre-commit install
