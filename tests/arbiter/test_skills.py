"""Tests for Arbiter skill loading and LLM client."""

from __future__ import annotations

from pathlib import Path

import pytest

from briefchain.arbiter.llm.client import LLMClient, LLMConfigurationError
from briefchain.arbiter.skills.loader import load_brief_review_skill
from briefchain.arbiter.skills.schemas import BriefReviewResult


def test_load_brief_review_skill() -> None:
    """The brief-review skill can be loaded from the local skill directory."""
    skill = load_brief_review_skill()

    assert skill.frontmatter.name == "brief-review"
    assert "Req Check" in skill.instructions
    assert "Why" in skill.instructions
    assert "What" in skill.instructions
    assert "Goals" in skill.instructions
    assert "Hypothesis" in skill.instructions


def test_load_brief_review_skill_with_custom_dir(tmp_path: Path) -> None:
    """A skill can be loaded from an arbitrary directory."""
    skill_dir = tmp_path / "custom-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: custom-skill\ndescription: test skill\n---\n\n# Instructions\nTest.\n"
    )

    skill = load_brief_review_skill(skill_dir)

    assert skill.frontmatter.name == "custom-skill"
    assert "Instructions" in skill.instructions


def test_llm_client_missing_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLMClient raises when LLM_BASE_URL is missing."""
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_base_url", None)
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_api_key", "key")
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_model", "model")

    with pytest.raises(LLMConfigurationError, match="LLM_BASE_URL"):
        LLMClient()


def test_llm_client_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLMClient raises when LLM_API_KEY is missing."""
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_base_url", "http://localhost")
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_api_key", None)
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_model", "model")

    with pytest.raises(LLMConfigurationError, match="LLM_API_KEY"):
        LLMClient()


def test_llm_client_missing_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLMClient raises when LLM_MODEL is missing."""
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_base_url", "http://localhost")
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_api_key", "key")
    monkeypatch.setattr("briefchain.arbiter.llm.client.settings.llm_model", None)

    with pytest.raises(LLMConfigurationError, match="LLM_MODEL"):
        LLMClient()


def test_brief_review_result_defaults() -> None:
    """BriefReviewResult can be constructed with required fields only."""
    result = BriefReviewResult(thinking="looks good", passed=True, score=80)

    assert result.passed is True
    assert result.score == 80
    assert result.issues == []
    assert result.suggestions == []


async def test_llm_client_fallback_to_json_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """When beta.chat.completions.parse fails, client falls back to JSON mode."""
    import json as json_module
    from unittest.mock import AsyncMock

    from openai import APIError

    client = LLMClient(base_url="http://localhost", api_key="key", model="qwen")

    parsed_response = BriefReviewResult(
        thinking="ok", passed=True, score=80, issues=[], suggestions=[]
    )

    # First call to parse fails; second call to create succeeds.
    mock_parse = AsyncMock(
        side_effect=APIError(
            message="not found",
            request=AsyncMock(),
            body=None,
        )
    )
    mock_create = AsyncMock()
    mock_create.return_value.choices = [
        AsyncMock(message=AsyncMock(content=json_module.dumps(parsed_response.model_dump())))
    ]

    monkeypatch.setattr(client._client.beta.chat.completions, "parse", mock_parse)
    monkeypatch.setattr(client._client.chat.completions, "create", mock_create)

    result = await client.generate_structured(
        "You are a reviewer.", "Brief content.", BriefReviewResult
    )

    assert result.passed is True
    assert result.score == 80
    mock_parse.assert_awaited_once()
    mock_create.assert_awaited_once()


async def test_llm_client_fallback_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """When both parse and JSON mode fail, LLMConfigurationError is raised."""
    from unittest.mock import AsyncMock

    from openai import APIError

    client = LLMClient(base_url="http://localhost", api_key="key", model="qwen")

    mock_parse = AsyncMock(
        side_effect=APIError(
            message="not found",
            request=AsyncMock(),
            body=None,
        )
    )
    mock_create = AsyncMock(
        side_effect=APIError(
            message="bad request",
            request=AsyncMock(),
            body=None,
        )
    )

    monkeypatch.setattr(client._client.beta.chat.completions, "parse", mock_parse)
    monkeypatch.setattr(client._client.chat.completions, "create", mock_create)

    with pytest.raises(LLMConfigurationError):
        await client.generate_structured(
            "You are a reviewer.", "Brief content.", BriefReviewResult
        )
