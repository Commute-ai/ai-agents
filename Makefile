PORT := 8000
HOST := 0.0.0.0

.PHONY: help
help:
	@echo "available commands:"
	@echo "  dev           - run development server with auto-reload"

.PHONY: dev
dev:
	@echo "🔄 Starting development server on http://$(HOST):$(PORT)"
	uv run uvicorn app.main:app --reload --host $(HOST) --port $(PORT)

.PHONY: test
test:
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v

.PHONY: test-cov
test-cov:
	@echo "🧪 Running tests with coverage..."
	uv run pytest tests/ --cov=app --cov-report=html --cov-report=term

.PHONY: lint
lint:
	@echo "🔍 Linting code..."
	uv run flake8 app/ tests/
	uv run mypy app/
	uv run black --check app/ tests/
	uv run isort --check-only app/ tests/

.PHONY: format
format:
	@echo "✨ Formatting code..."
	uv run black app/ tests/
	uv run isort app/ tests/
