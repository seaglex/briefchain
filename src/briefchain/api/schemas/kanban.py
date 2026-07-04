"""Pydantic schemas for kanban and kanban template endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from briefchain.models.enums import (
    KanbanGroup,
    KanbanOwnerType,
    KanbanTemplateMode,
)
from briefchain.api.schemas.tasks import TaskListItem


# ---------------------------------------------------------------------------
# Shared column schemas
# ---------------------------------------------------------------------------


class KanbanTemplateColumnResponse(BaseModel):
    """A column definition as returned by config/template endpoints."""

    model_config = ConfigDict(from_attributes=True)

    column_id: int
    status_key: str
    name: str
    color: str | None
    is_hidden: bool
    position: int


class KanbanColumnResponse(KanbanTemplateColumnResponse):
    """A board column that also contains swimlanes."""

    swimlanes: list["KanbanSwimlaneResponse"]


# ---------------------------------------------------------------------------
# Board response
# ---------------------------------------------------------------------------


class KanbanSummary(BaseModel):
    """Minimal kanban info returned with a board query."""

    model_config = ConfigDict(from_attributes=True)

    kanban_id: int
    kanban_template_id: int
    kanban_template_mode: KanbanTemplateMode
    group: KanbanGroup
    done_visible_days: int
    is_default: bool


class KanbanSwimlaneResponse(BaseModel):
    """A swimlane within a board column."""

    swimlane_key: str | None
    tasks: list[TaskListItem]


class KanbanBoardResponse(BaseModel):
    """Full personal kanban board response."""

    kanban: KanbanSummary
    columns: list[KanbanColumnResponse]


# ---------------------------------------------------------------------------
# Kanban config request/response
# ---------------------------------------------------------------------------


class KanbanConfig(BaseModel):
    """Kanban instance configuration."""

    model_config = ConfigDict(from_attributes=True)

    kanban_id: int
    kanban_template_id: int
    name: str
    owner_type: KanbanOwnerType
    owner_id: UUID
    group: KanbanGroup
    done_visible_days: int
    is_default: bool
    created_at: datetime
    updated_at: datetime


class KanbanTemplateSummary(BaseModel):
    """Minimal template info returned inside kanban config."""

    model_config = ConfigDict(from_attributes=True)

    kanban_template_id: int
    name: str
    kanban_template_mode: KanbanTemplateMode
    created_by: UUID


class KanbanConfigResponse(BaseModel):
    """Kanban configuration page response."""

    kanban: KanbanConfig
    template: KanbanTemplateSummary
    columns: list[KanbanTemplateColumnResponse]


class KanbanUpdateRequest(BaseModel):
    """Request body for updating kanban-level settings."""

    name: str | None = None
    kanban_template_id: int | None = None
    group: KanbanGroup | None = None
    done_visible_days: int | None = None


class KanbanCreateRequest(BaseModel):
    """Request body for creating a kanban board."""

    owner_type: KanbanOwnerType
    owner_id: UUID
    kanban_template_id: int
    group: KanbanGroup | None = KanbanGroup.NONE
    done_visible_days: int | None = 14
    is_default: bool | None = False


# ---------------------------------------------------------------------------
# Column update request/response
# ---------------------------------------------------------------------------


class KanbanColumnUpdateItem(BaseModel):
    """A single column inside a full column-update request."""

    column_id: int | None = None
    status_key: str
    name: str
    color: str | None = None
    is_hidden: bool
    position: int


class KanbanColumnsUpdateRequest(BaseModel):
    """Request body for replacing a kanban's column configuration."""

    name: str | None = None
    kanban_template_mode: KanbanTemplateMode | None = None
    is_public: bool | None = None
    columns: list[KanbanColumnUpdateItem]


class KanbanColumnsUpdateResponse(BaseModel):
    """Response after updating kanban columns."""

    kanban: KanbanConfig
    columns: list[KanbanTemplateColumnResponse]


# ---------------------------------------------------------------------------
# Kanban template request/response
# ---------------------------------------------------------------------------


class KanbanTemplateListItem(BaseModel):
    """Template list item."""

    model_config = ConfigDict(from_attributes=True)

    kanban_template_id: int
    name: str
    kanban_template_mode: KanbanTemplateMode
    created_by: UUID
    created_by_name: str
    is_public: bool
    created_at: datetime
    updated_at: datetime


class KanbanTemplateListResponse(BaseModel):
    """Paginated list of kanban templates."""

    templates: list[KanbanTemplateListItem]
    next_cursor: str | None


class KanbanTemplateDetailResponse(BaseModel):
    """Template detail with columns."""

    template: KanbanTemplateListItem
    columns: list[KanbanTemplateColumnResponse]


KanbanColumnResponse.model_rebuild()
