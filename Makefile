PORT := 8001
HOST := 0.0.0.0

.PHONY: help
help:
	@echo "available commands:"
	@echo "  dev           - run development server with auto-reload"
	@echo "  test          - run tests"
	@echo "  test-cov      - run tests with coverage"
	@echo "  lint          - run linter"
	@echo "  format        - run formatter"
	@echo "  docker-build  - build Docker image"
	@echo "  docker-up     - start with Docker Compose"
	@echo "  docker-down   - stop Docker Compose"
	@echo "  docker-logs   - show Docker logs"

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
	uv run ruff check app/ tests/
	uv run ruff format --check app/ tests/
	uv run mypy app/

.PHONY: format
format:
	@echo "✨ Formatting code..."
	uv run ruff check --fix app/ tests/
	uv run ruff format app/ tests/

# Docker

.PHONY: docker-build
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t commute-ai-ai-agents .

.PHONY: docker-up
docker-up:
	@echo "🐳 Starting with Docker Compose..."
	docker compose up -d

.PHONY: docker-down
docker-down:
	@echo "🐳 Stopping Docker Compose..."
	docker compose down

.PHONY: docker-logs
docker-logs:
	@echo "📋 Showing Docker logs..."
	docker compose logs -f


