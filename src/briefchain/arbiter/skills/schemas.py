"""Structured output schemas for Arbiter skills."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BriefReviewResult(BaseModel):
    """Structured result from the ``brief-review`` skill."""

    thinking: str = Field(
        ...,
        description="Reasoning process used to evaluate the brief.",
    )
    passed: bool = Field(
        ...,
        description="Whether the brief passed the quality review.",
    )
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Quality score from 0 to 100.",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="List of problems found in the brief.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable suggestions to improve the brief.",
    )
