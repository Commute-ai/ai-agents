"""
FastAPI dependency injection for application services.
"""

from app.services.insight import InsightService


def get_insight_service() -> InsightService:
    return InsightService()
