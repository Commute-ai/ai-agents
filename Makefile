PORT := 8001
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


