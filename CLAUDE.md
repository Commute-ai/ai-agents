# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- `uv sync --dev` - Install dependencies and sync lockfile
- `nix-shell` - Alternative setup using Nix (provides Python 3.11, uv, and activates environment)

### Common Development Tasks
- `make dev` - Start development server on http://0.0.0.0:8001 with auto-reload
- `make test` - Run all tests with pytest
- `make test-cov` - Run tests with coverage reporting (HTML and terminal output)
- `make lint` - Check code quality with ruff and mypy
- `make format` - Format code with ruff (includes auto-fixing and formatting)

### Running Individual Tests
- `uv run pytest tests/endpoints/test_health.py` - Run specific test file
- `uv run pytest tests/endpoints/test_health.py::test_health_check` - Run specific test function
- `uv run pytest -k "health"` - Run tests matching pattern

### Code Quality Tools
- **Linting**: Uses ruff for linting and formatting (replaces black, flake8, isort)
- **Type Checking**: Uses mypy for static type analysis
- **Testing**: Uses pytest with asyncio support for FastAPI testing

## Architecture Overview

### FastAPI Application Structure
This is a FastAPI-based API service for AI-powered route analysis and recommendations.

**Core Application Flow:**
- `app/main.py` - FastAPI application entry point with CORS middleware
- `app/config.py` - Centralized settings using pydantic-settings with .env support
- `app/api/v1/routes.py` - Main router that aggregates all endpoint routers

### API Architecture
- **Versioned API**: All endpoints under `/api/v1` prefix
- **Modular Endpoints**: Each feature has its own router in `app/api/v1/endpoints/`
- **Current Endpoints**:
  - Health check: `GET /api/v1/health` 
  - Insights: `POST /api/v1/itineraries` (generates AI insights for route itineraries)

### Schema Design
Located in `app/schemas/`, uses Pydantic for data validation:

- **Itinerary System**: Core models for representing transit routes
  - `Itinerary` - Complete journey with legs, duration, walking metrics
  - `ItineraryWithInsight` - Extends Itinerary with AI-generated insights
  - `Leg` - Individual journey segments with transport modes, places, routes
  - `TransportMode` - Enum for different transit types (WALK, BUS, RAIL, etc.)

- **Request/Response Models**: Defined inline in endpoint files
  - `ItinerariesRequest` - Takes list of itineraries + optional user preferences
  - `ItinerariesResponse` - Returns itineraries enhanced with AI insights

### Key Architectural Patterns
- **Dependency Injection**: Uses FastAPI's DI system for configuration and services
- **Async Support**: Configured for async/await patterns with pytest-asyncio
- **Modular Schema**: Separate schema files that compose together (itinerary uses location, etc.)

### Testing Structure
- `tests/conftest.py` - Shared fixtures including TestClient for FastAPI testing
- Endpoint tests in `tests/endpoints/` mirror the API structure
- Uses session-scoped anyio_backend fixture for async test support

### Development Environment
- **Python**: Requires Python 3.11+
- **Package Management**: Uses uv for fast dependency management
- **Nix Support**: shell.nix provides reproducible development environment
- **Docker**: Dockerfile and docker-compose.yml for containerized deployment

## Project Context
This is part of the Commute.ai ecosystem focused on AI-powered transportation recommendations. The current implementation provides placeholder AI insights but is structured to integrate real AI analysis of transit itineraries based on user preferences.
- Never put code in __init__ files