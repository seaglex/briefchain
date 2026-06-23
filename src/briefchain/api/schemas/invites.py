"""Pydantic schemas for invite endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from briefchain.api.schemas.briefs import BriefDetail


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


class InviteViewResponse(BaseModel):
    """Response returned by GET /invites/{token}."""

    model_config = ConfigDict(from_attributes=True)

    invite: InviteMetadata
    brief: BriefDetail


class AcceptInviteRequest(BaseModel):
    """Optional body for accepting an invite; allows correcting the recipient name."""

    name: str | None = Field(default=None, min_length=1, max_length=255)


class RejectInviteRequest(BaseModel):
    """Body for rejecting an invite."""

    reason: str = Field(..., min_length=1)


class BlockedInviteRequest(BaseModel):
    """Body for marking a brief as blocked via an invite."""

    reason: str = Field(..., min_length=1)


class DoneInviteRequest(BaseModel):
    """Body for marking a brief as done via an invite."""

    result: str = Field(..., min_length=1)
