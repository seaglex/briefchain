"""LLM client wrapper for Arbiter skill invocation."""

from __future__ import annotations

import json
from typing import TypeVar

from openai import APIError, AsyncOpenAI
from pydantic import BaseModel, ValidationError

from briefchain.api.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMConfigurationError(RuntimeError):
    """Raised when required LLM configuration is missing."""


class LLMClient:
    """Thin wrapper around an OpenAI-compatible LLM API."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize the client with optional overrides.

        Args:
            base_url: API base URL. Defaults to ``settings.llm_base_url``.
            api_key: API key. Defaults to ``settings.llm_api_key``.
            model: Model identifier. Defaults to ``settings.llm_model``.

        Raises:
            LLMConfigurationError: If any required setting is missing.
        """
        self.base_url = base_url if base_url is not None else settings.llm_base_url
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.model = model if model is not None else settings.llm_model

        if not self.base_url:
            raise LLMConfigurationError("LLM_BASE_URL is not configured")
        if not self.api_key:
            raise LLMConfigurationError("LLM_API_KEY is not configured")
        if not self.model:
            raise LLMConfigurationError("LLM_MODEL is not configured")

        self._client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)

    async def generate_structured(
        self,
        system_prompt: str,
        user_content: str,
        output_schema: type[T],
    ) -> T:
        """Generate a structured response from the LLM.

        Args:
            system_prompt: System prompt defining the skill behavior.
            user_content: User content to evaluate (e.g. brief content).
            output_schema: Pydantic model describing the expected output.

        Returns:
            Parsed structured output matching ``output_schema``.
        """
        try:
            return await self._generate_with_parse(system_prompt, user_content, output_schema)
        except APIError as exc:
            # OpenAI's beta parse endpoint is not supported by many third-party
            # providers (e.g. Qwen/DashScope). Fall back to JSON-mode generation.
            return await self._generate_with_json_mode(
                system_prompt, user_content, output_schema, original_error=exc
            )

    async def _generate_with_parse(
        self,
        system_prompt: str,
        user_content: str,
        output_schema: type[T],
    ) -> T:
        """Use OpenAI's structured-output parse endpoint."""
        completion = await self._client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format=output_schema,
        )
        message = completion.choices[0].message
        if message.refusal:
            raise LLMConfigurationError(f"LLM refused the request: {message.refusal}")
        if message.parsed is None:
            raise LLMConfigurationError("LLM returned no parsed output")
        return message.parsed

    async def _generate_with_json_mode(
        self,
        system_prompt: str,
        user_content: str,
        output_schema: type[T],
        original_error: APIError | None = None,
    ) -> T:
        """Fallback for providers that do not support ``beta.chat.completions.parse``.

        Injects the JSON schema into the system prompt and requests JSON output.
        """
        schema = output_schema.model_json_schema()
        enhanced_prompt = (
            f"{system_prompt}\n\n"
            f"You must respond with a single JSON object matching this schema:\n"
            f"```json\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n```\n"
            f"Do not include any markdown formatting, explanation, or text outside the JSON object."
        )

        try:
            completion = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
        except APIError as exc:
            if original_error is not None:
                raise LLMConfigurationError(
                    f"Structured output failed ({original_error}) and JSON mode also failed: {exc}"
                ) from exc
            raise

        content = completion.choices[0].message.content
        if content is None:
            raise LLMConfigurationError("LLM returned empty content")

        try:
            return output_schema.model_validate_json(content)
        except ValidationError as exc:
            raise LLMConfigurationError(
                f"LLM response did not match expected schema: {exc}"
            ) from exc


def get_default_client() -> LLMClient:
    """Return an LLM client configured from environment variables."""
    return LLMClient()
