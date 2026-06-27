"""Pydantic schemas for feedback endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from briefchain.models.enums import FeedbackType


class UserRef(BaseModel):
    """Minimal user reference returned inside feedback responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class FeedbackCreateRequest(BaseModel):
    """Request body for creating feedback.

    Deprecated in the public API: feedbacks are now created by lifecycle endpoints.
    Kept for internal service use.
    """

    type: FeedbackType
    content: str = Field(..., min_length=1)
    attachments: list[dict] = Field(default_factory=list)


class FeedbackListItem(BaseModel):
    """Feedback list mode response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brief_id: UUID
    brief_version: int
    is_to_down: bool
    type: FeedbackType
    from_user_id: UUID
    from_user_name: str
    to_user_id: UUID
    to_user_name: str
    created_at: str


class FeedbackDetail(FeedbackListItem):
    """Feedback detail mode response."""

    content: str
    attachments: list[dict]
    is_auto_generated: bool
    confirmed_at: str | None
