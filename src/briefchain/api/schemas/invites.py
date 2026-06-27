"""Pydantic schemas for invite endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InviteUserRef(BaseModel):
    """Minimal user reference returned inside invite responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class InviteMetadata(BaseModel):
    """Public invite metadata shown to the recipient."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    from_user: InviteUserRef
    accept_deadline: str
    complete_deadline: str


class InviteMetadataResponse(BaseModel):
    """Invite metadata returned when sending a brief to an external user."""

    model_config = ConfigDict(from_attributes=True)

    invite_url: str
    accept_deadline: str
    complete_deadline: str


class AcceptInviteRequest(BaseModel):
    """Optional body for accepting an invite; allows correcting the recipient name."""

    name: str | None = Field(default=None, min_length=1, max_length=255)


class RejectInviteRequest(BaseModel):
    """Body for rejecting an invite."""

    reason: str = Field(..., min_length=1)


class SubmitInviteRequest(BaseModel):
    """Body for submitting completion via an invite."""

    content: str = Field(..., min_length=1)
    attachments: list[dict] | None = None


class BlockInviteRequest(BaseModel):
    """Body for marking a brief as blocked via an invite."""

    reason: str = Field(..., min_length=1)
    attachments: list[dict] | None = None


class OpenInviteRequest(BaseModel):
    """Body for reopening a brief via an invite."""

    reason: str = Field(..., min_length=1)


class DelegateInviteRequest(BaseModel):
    """Body for delegating a brief via an invite."""

    content: str | None = Field(default=None)
