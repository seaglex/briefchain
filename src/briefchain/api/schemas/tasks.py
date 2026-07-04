"""Pydantic schemas for task and task comment endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from briefchain.models.enums import KanbanGroup, TaskPriority, TaskStatus, TaskType


# ---------------------------------------------------------------------------
# Task request schemas
# ---------------------------------------------------------------------------


class TaskCreateRequest(BaseModel):
    """Request body for creating a task."""

    brief_id: UUID | None = None
    type: TaskType
    parent_task_id: int | None = None
    team_id: UUID | None = None

    title: str
    content: str | None = None

    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: UUID | None = None
    estimated_hours: int | None = None
    due_date: datetime | None = None


class TaskUpdateRequest(BaseModel):
    """Request body for updating a task."""

    title: str | None = None
    content: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: UUID | None = None
    estimated_hours: int | None = None
    actual_hours: int | None = None
    due_date: datetime | None = None


class TaskDragRequest(BaseModel):
    """Request body for dragging a task to a new column."""

    status: TaskStatus
    assignee_id: UUID | None = None
    column_id: int | None = None
    position: int | None = None


# ---------------------------------------------------------------------------
# Task comment schemas
# ---------------------------------------------------------------------------


class TaskCommentCreateRequest(BaseModel):
    """Request body for creating a task comment."""

    content: str


class TaskCommentResponse(BaseModel):
    """Task comment representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    created_by: UUID
    created_by_name: str
    created_at: datetime
    updated_at: datetime


class TaskCommentListResponse(BaseModel):
    """Paginated list of task comments."""

    comments: list[TaskCommentResponse]
    next_cursor: str | None


# ---------------------------------------------------------------------------
# Task response schemas
# ---------------------------------------------------------------------------


class TaskListItem(BaseModel):
    """Lightweight task representation for lists and kanban cards."""

    model_config = ConfigDict(from_attributes=True)

    task_id: int
    type: TaskType
    title: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: UUID | None
    assignee_name: str | None
    brief_id: UUID | None
    updated_at: datetime


class TaskDetail(BaseModel):
    """Full task representation including content and metadata."""

    model_config = ConfigDict(from_attributes=True)

    task_id: int
    brief_id: UUID | None
    parent_task_id: int | None
    team_id: UUID | None

    type: TaskType
    title: str
    content: str | None

    status: TaskStatus
    priority: TaskPriority

    assignee_id: UUID | None
    assignee_name: str | None

    estimated_hours: int | None
    actual_hours: int | None
    due_date: datetime | None

    status_changed_by: UUID | None
    status_changed_at: datetime | None

    created_by: UUID
    created_by_name: str
    created_at: datetime
    updated_at: datetime

    is_deleted: bool
    deleted_by: UUID | None
    deleted_at: datetime | None


class TaskDetailResponse(BaseModel):
    """Task detail response including sub-tasks and comments."""

    task: TaskDetail
    sub_tasks: list[TaskListItem]
    comments: list[TaskCommentResponse]


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    tasks: list[TaskListItem]
    next_cursor: str | None
