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
    """Request body for creating feedback."""

    type: FeedbackType
    content: str = Field(..., min_length=1)
    attachments: list[dict] = Field(default_factory=list)


class FeedbackListItem(BaseModel):
    """Feedback list mode response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: FeedbackType
    from_user: UserRef
    created_at: str


class FeedbackDetail(FeedbackListItem):
    """Feedback detail mode response."""

    brief_id: UUID
    brief_version: int
    content: str
    attachments: list[dict]
    confirmed_at: str | None
