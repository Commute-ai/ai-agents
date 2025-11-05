"""
Base agent class for AI-powered tasks.
"""

import importlib.resources
from typing import ClassVar

import jinja2
from pydantic import BaseModel

from app.services.llm.base import LLMProvider


class BaseAgent:
    """
    Simplified base agent for AI-powered tasks.

    Agents define their input and output types as class attributes and load
    their configuration and templates from their module directory.
    """

    # Subclasses should define these
    input_model: ClassVar[type[BaseModel]]
    output_model: ClassVar[type[BaseModel]]

    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the agent with an LLM provider.

        Args:
            llm_provider: The LLM provider to use for generation
        """
        self.llm_provider = llm_provider

    async def execute(self, input_data: BaseModel) -> BaseModel:
        """
        Execute the agent with input data and return structured output.

        Args:
            input_data: Input data as a Pydantic model

        Returns:
            Generated output as the defined output model type
        """
        # Validate input type
        if not isinstance(input_data, self.input_model):
            raise AgentValidationError(
                f"Expected input of type {self.input_model.__name__}, "
                f"got {type(input_data).__name__}"
            )

        # Load agent templates
        system_template = self._load_template("prompts/system.j2")
        user_template = self._load_template("prompts/user.j2")

        # Render prompts with input data
        system_prompt = system_template.render(**input_data.model_dump())
        user_prompt = user_template.render(**input_data.model_dump())

        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Generate response (LLM provider handles its own configuration)
        response = await self.llm_provider.generate(messages)

        # Parse and validate response
        try:
            return self.output_model.model_validate_json(response)
        except Exception as e:
            raise AgentProcessingError(
                f"Failed to parse response as {self.output_model.__name__}: {e}"
            ) from e

    def _load_template(self, template_name: str) -> jinja2.Template:
        """Load and compile a Jinja2 template."""
        try:
            # Get the agent's module directory
            agent_module = self.__class__.__module__
            if agent_module.endswith("insight"):
                pkg = importlib.resources.files("app.agents.insight")
            else:
                agent_package = agent_module.rsplit(".", 1)[0]
                pkg = importlib.resources.files(agent_package)

            template_text = (pkg / template_name).read_text()
            return jinja2.Template(template_text)
        except (FileNotFoundError, jinja2.TemplateError) as e:
            raise AgentValidationError(f"Failed to load template {template_name}: {e}") from e


class AgentError(Exception):
    """Base exception for agent errors."""

    pass


class AgentValidationError(AgentError):
    """Raised when agent input validation fails."""

    pass


class AgentProcessingError(AgentError):
    """Raised when agent processing fails."""

    pass
