"""
FastAPI dependency injection for application services.
"""

from typing import Annotated

from fastapi import Depends

from app.agents.insight import InsightAgent
from app.services.llm.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    """
    Get the LLM provider instance.

    This dependency will be initialized once at startup and reused
    across all requests through FastAPI's dependency caching.

    Returns:
        The singleton LLM provider instance
    """
    from app.main import app

    return app.state.llm_provider


# Type alias for LLM provider dependency
LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]


def get_insight_agent(llm_provider: LLMProviderDep) -> InsightAgent:
    """
    Get an InsightAgent instance with the injected LLM provider.

    Args:
        llm_provider: The LLM provider dependency

    Returns:
        An initialized InsightAgent instance
    """
    return InsightAgent(llm_provider)


# Type alias for InsightAgent dependency
InsightAgentDep = Annotated[InsightAgent, Depends(get_insight_agent)]
