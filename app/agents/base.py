from __future__ import annotations

import importlib.resources
import json
from typing import (
    Generic,
    Iterable,
    TypeVar,
    cast,
)

import jinja2
import openai
from openai.types.chat import ChatCompletionMessageParam
from openai.types.shared_params import ResponseFormatJSONSchema
from pydantic import BaseModel

from app.config import settings

InT = TypeVar("InT", bound=BaseModel)
OutT = TypeVar("OutT", bound=BaseModel)


class BaseAgent(Generic[InT, OutT]):
    @classmethod
    def __class_getitem__(cls, args: tuple[type[BaseModel], type[BaseModel]]):
        if not isinstance(args, tuple):
            args = (args,)
        if len(args) != 2:
            raise TypeError("BaseAgent requires exactly two type parameters")

        in_t, out_t = args

        class BoundBaseAgent:
            @classmethod
            def execute(cls, arg: InT) -> OutT:
                if not isinstance(arg, in_t):
                    raise TypeError(
                        f"Expected argument of type "
                        f"'{in_t.__module__}.{in_t.__name__}', "
                        f"got {type(arg)}"
                    )

                agent_package = cls.__module__.rsplit(".", 1)[0]
                pkg = importlib.resources.files(agent_package)

                config = (pkg / "config.json").read_text()
                system_template = (pkg / "system.j2").read_text()
                user_template = (pkg / "user.j2").read_text()

                try:
                    model_config = json.loads(config)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in agent config file: {e}")

                try:
                    system_prompt_template = jinja2.Template(system_template)
                except jinja2.TemplateError as e:
                    raise ValueError(f"Invalid Jinja2 template in system prompt file: {e}")

                try:
                    user_prompt_template = jinja2.Template(user_template)
                except jinja2.TemplateError as e:
                    raise ValueError(f"Invalid Jinja2 template in user prompt file: {e}")

                client = openai.OpenAI(
                    base_url=settings.OPENAI_BASE_URL, api_key=settings.OPENAI_API_KEY
                )

                REQUIRED_CONFIG_KEYS = {"model"}
                ALLOWED_CONFIG_KEYS = {
                    "model",
                    "temperature",
                    "max_completion_tokens",
                    "top_p",
                    "reasoning_effort",
                }

                missing_keys = REQUIRED_CONFIG_KEYS - model_config.keys()
                if missing_keys:
                    raise ValueError(
                        f"Missing required model configuration keys: " f"{', '.join(missing_keys)}"
                    )

                extra_keys = set(model_config.keys()) - ALLOWED_CONFIG_KEYS
                if extra_keys:
                    raise ValueError(
                        f"Unknown model configuration keys: " f"{', '.join(extra_keys)}"
                    )

                model_config = {k: v for k, v in model_config.items() if k in ALLOWED_CONFIG_KEYS}

                system_prompt = system_prompt_template.render(**arg.model_dump())
                user_prompt = user_prompt_template.render(**arg.model_dump())

                response = client.chat.completions.create(
                    **model_config,
                    messages=cast(
                        Iterable[ChatCompletionMessageParam],
                        [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    ),
                    stream=False,
                    response_format=cast(
                        ResponseFormatJSONSchema,
                        {
                            "type": "json_schema",
                            "json_schema": {
                                "name": out_t.__name__,
                                "schema": out_t.model_json_schema(),
                            },
                        },
                    ),
                )

                choice = response.choices[0].message
                content = getattr(choice, "content", None)
                if not content:
                    raise ValueError("Empty assistant content; cannot validate as JSON.")
                if isinstance(content, list):
                    content = "".join(p.get("text", "") for p in content)

                content = content.strip()
                return cast(OutT, out_t.model_validate_json(content))

        return BoundBaseAgent

    @classmethod
    def execute(cls, arg: InT) -> OutT:
        raise RuntimeError("BaseAgent cannot be executed")
