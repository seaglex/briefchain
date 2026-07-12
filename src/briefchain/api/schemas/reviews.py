"""Request and response schemas for Arbiter review endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from briefchain.models.enums import ArbiterReviewStatus


class ReviewCreateRequest(BaseModel):
    """Request body for triggering a new review."""

    webhook_url: str | None = Field(
        default=None,
        description="Optional webhook URL for review notifications.",
    )


class ReviewResponse(BaseModel):
    """Response schema for a review, including terminal-state details."""

    model_config = ConfigDict(from_attributes=True)

    review_id: UUID
    brief_id: UUID
    brief_version: int
    status: ArbiterReviewStatus
    attempt_count: int
    created_at: datetime

    arbiter_id: str | None = None
    score: int | None = None
    issues: list[dict] | None = None
    suggestions: list[str] | None = None
    error: str | None = None
    reviewed_at: datetime | None = None


class ReviewAcceptedResponse(BaseModel):
    """Response returned when a review is accepted for async processing."""

    review_id: UUID
    brief_id: UUID
    brief_version: int
    status: ArbiterReviewStatus
    created_at: datetime
