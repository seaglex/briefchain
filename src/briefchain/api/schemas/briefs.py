"""Pydantic schemas for brief endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from briefchain.models.enums import BriefPriority, BriefStatus


class UserRef(BaseModel):
    """Minimal user reference returned inside brief responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class BriefListItem(BaseModel):
    """Brief list mode response."""

    model_config = ConfigDict(from_attributes=True)

    brief_id: UUID
    title: str
    status: BriefStatus
    priority: BriefPriority
    created_by: UserRef
    assigned_to: UserRef | None
    updated_at: str


class BriefDetail(BriefListItem):
    """Brief detail mode response including version content."""

    root_id: UUID
    parent_id: UUID | None
    content: str
    attachments: list[dict]
    current_version: int
    version: int
    is_current: bool
    estimated_man_days: float | None
    created_at: str


class BriefVersionListItem(BaseModel):
    """Brief version list item."""

    model_config = ConfigDict(from_attributes=True)

    version: int
    title: str
    modified_by: UserRef
    modified_at: str
    change_summary: str
    is_upstream_changed: bool
    revision_reason: str


class BriefVersionDetail(BriefDetail):
    """Specific version detail response."""

    pass


class BriefCreateRequest(BaseModel):
    """Request body for creating a brief."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    attachments: list[dict] = Field(default_factory=list)
    priority: BriefPriority = BriefPriority.P2
    estimated_man_days: float | None = Field(default=None, ge=0)
    parent_id: UUID | None = None


class BriefUpdateRequest(BaseModel):
    """Request body for updating a draft brief."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    attachments: list[dict] | None = None
    priority: BriefPriority | None = None
    estimated_man_days: float | None = Field(default=None, ge=0)
    is_upstream_changed: bool | None = None
    revision_reason: str | None = Field(default=None, min_length=1, max_length=255)
    change_summary: str | None = Field(default=None, min_length=1)


class BriefTransferResponse(BaseModel):
    """Transfer record included in lifecycle responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brief_version: int
    from_user: UserRef
    to_user: UserRef
    sent_at: str
    accepted_at: str | None
    rejected_at: str | None
    rejection_reason: str | None


class BriefLifecycleResponse(BaseModel):
    """Response returned by brief lifecycle endpoints."""

    brief: BriefDetail
    transfer: BriefTransferResponse | None = None
    message: str | None = None
