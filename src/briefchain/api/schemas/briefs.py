"""Pydantic schemas for brief endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from briefchain.models.enums import (
    BriefDownstreamState,
    BriefPriority,
    BriefUpstreamState,
    BriefVersionStatus,
)


class UserSnapshot(BaseModel):
    """Flat user snapshot returned inside brief responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class BriefListItem(BaseModel):
    """Brief list mode response."""

    model_config = ConfigDict(from_attributes=True)

    brief_id: UUID
    title: str
    upstream_state: BriefUpstreamState
    downstream_state: BriefDownstreamState | None
    priority: BriefPriority
    created_by_id: UUID
    created_by_name: str
    assigned_to_id: UUID | None
    assigned_to_name: str | None
    status_changed_by_id: UUID
    status_changed_by_name: str
    status_changed_at: str
    updated_at: str


class BriefDetail(BriefListItem):
    """Brief detail mode response including version content."""

    root_id: UUID
    parent_id: UUID | None
    content: str
    attachments: list[dict]
    current_version: int | None
    current_version_status: BriefVersionStatus | None
    version: int
    is_current: bool
    unfinalized_version: int | None
    estimated_man_days: float | None
    expected_completion_at: str | None
    created_at: str


class BriefVersionListItem(BaseModel):
    """Brief version list item."""

    model_config = ConfigDict(from_attributes=True)

    version: int
    status: BriefVersionStatus
    title: str
    modified_by_id: UUID
    modified_by_name: str
    modified_at: str
    change_summary: str
    is_upstream_changed: bool
    revision_reason: str


class BriefCreateRequest(BaseModel):
    """Request body for creating a brief."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    attachments: list[dict] = Field(default_factory=list)
    priority: BriefPriority = BriefPriority.P2
    estimated_man_days: float | None = Field(default=None, ge=0)
    expected_completion_at: str | None = Field(default=None)
    parent_id: UUID | None = None


class BriefPatchRequest(BaseModel):
    """Request body for patching a draft brief."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    attachments: list[dict] | None = None
    priority: BriefPriority | None = None
    estimated_man_days: float | None = Field(default=None, ge=0)
    expected_completion_at: str | None = Field(default=None)
    revision_reason: str | None = Field(default=None, min_length=1, max_length=255)
    change_summary: str | None = Field(default=None, min_length=1)


class BriefReviewRequest(BaseModel):
    """Request body for submitting a draft version for review."""

    note: str | None = Field(default=None)


class BriefUpdateActionRequest(BaseModel):
    """Request body for pushing an updated brief version (upstream-actions update)."""

    version: int = Field(..., ge=1)
    content: str = Field(..., min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    attachments: list[dict] | None = None
    priority: BriefPriority | None = None
    estimated_man_days: float | None = Field(default=None, ge=0)
    expected_completion_at: str | None = Field(default=None)
    revision_reason: str | None = Field(default=None, min_length=1, max_length=255)
    change_summary: str | None = Field(default=None, min_length=1)


class SendBriefRegisteredRequest(BaseModel):
    """Request body for sending a brief to a registered user."""

    assigned_to: UUID
    note: str | None = None


class SendBriefExternalRequest(BaseModel):
    """Request body for sending a brief to an external user via invite."""

    recipient_email: str | None = Field(default=None, examples=["lisi@example.com"])
    recipient_phone: str | None = Field(default=None, examples=["+8613800000000"])
    recipient_name: str | None = Field(default=None, max_length=255)
    note: str | None = None
    accept_deadline_days: int = Field(default=7, ge=1)
    complete_deadline_days: int = Field(default=30, ge=1)


class SendBriefRequest(BaseModel):
    """Request body for sending a brief.

    When `is_temporary_user` is true, `recipient_email`/`recipient_phone` are
    optional and the system creates or reuses a temporary user. When false,
    `assigned_to` must be provided.
    """

    is_temporary_user: bool = False
    assigned_to: UUID | None = None
    recipient_email: str | None = Field(default=None, examples=["lisi@example.com"])
    recipient_phone: str | None = Field(default=None, examples=["+8613800000000"])
    recipient_name: str | None = Field(default=None, max_length=255)
    note: str | None = None
    accept_deadline_days: int = Field(default=7, ge=1)
    complete_deadline_days: int = Field(default=30, ge=1)

    @model_validator(mode="after")
    def validate_send_request(self) -> "SendBriefRequest":
        if self.is_temporary_user:
            return self
        if self.assigned_to is None:
            raise ValueError("assigned_to is required when is_temporary_user is false")
        return self


class AcceptTransferRequest(BaseModel):
    """Request body for accepting a sent brief."""

    note: str | None = Field(default=None)


class RejectTransferRequest(BaseModel):
    """Request body for rejecting a sent brief."""

    reason: str = Field(..., min_length=1)


class UpstreamActionRequest(BaseModel):
    """Request body for upstream-actions that require a content reason."""

    content: str = Field(..., min_length=1)


class DownstreamActionRequest(BaseModel):
    """Request body for downstream-actions."""

    content: str | None = Field(default=None)
    attachments: list[dict] | None = Field(default=None)


class BriefTransferResponse(BaseModel):
    """Transfer record included in lifecycle responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brief_version: int
    from_user_id: UUID
    from_user_name: str
    to_user_id: UUID
    to_user_name: str
    sent_at: str
    accepted_at: str | None
    rejected_at: str | None
    rejection_reason: str | None


class BriefLifecycleResponse(BaseModel):
    """Response returned by brief lifecycle endpoints."""

    brief: BriefDetail
    transfer: BriefTransferResponse | None = None
    feedback: dict | None = None
    message: str | None = None
    invite: dict | None = None
