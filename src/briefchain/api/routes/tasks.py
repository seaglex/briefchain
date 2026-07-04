"""Task and task comment routes for the BriefChain API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from briefchain.api.dependencies import CurrentUserIdDep, SessionDep, get_current_user_id
from briefchain.api.schemas.tasks import (
    TaskCommentCreateRequest,
    TaskCommentListResponse,
    TaskCommentResponse,
    TaskCreateRequest,
    TaskDetail,
    TaskDetailResponse,
    TaskDragRequest,
    TaskListResponse,
    TaskUpdateRequest,
)
from briefchain.api.services import tasks as task_service
from briefchain.models.enums import TaskPriority, TaskStatus, TaskType

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(get_current_user_id)],
)

comments_router = APIRouter(
    prefix="/comments",
    tags=["task-comments"],
    dependencies=[Depends(get_current_user_id)],
)


@router.post("", response_model=TaskDetail, status_code=status.HTTP_201_CREATED)
def create_task(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    request: TaskCreateRequest,
) -> TaskDetail:
    """Create a new task."""
    return task_service.create_task(session, user_id, request)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: Annotated[UUID | None, Query()] = None,
    task_type: Annotated[TaskType | None, Query(alias="type")] = None,
    status: Annotated[TaskStatus | None, Query()] = None,
    team_id: Annotated[UUID | None, Query()] = None,
    assignee_id: Annotated[UUID | None, Query()] = None,
    priority: Annotated[TaskPriority | None, Query()] = None,
    page_cursor: Annotated[str | None, Query()] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TaskListResponse:
    """List tasks with optional filters and cursor pagination."""
    return task_service.list_tasks(
        session,
        user_id,
        brief_id=brief_id,
        task_type=task_type,
        status=status,
        team_id=team_id,
        assignee_id=assignee_id,
        priority=priority,
        page_cursor=page_cursor,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(
    session: SessionDep,
    task_id: int,
) -> TaskDetailResponse:
    """Get a task with sub-tasks and latest comments."""
    return task_service.get_task_detail(session, task_id)


@router.put("/{task_id}", response_model=TaskDetail)
def update_task(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    task_id: int,
    request: TaskUpdateRequest,
) -> TaskDetail:
    """Update a task."""
    return task_service.update_task(session, task_id, user_id, request)


@router.put("/{task_id}/drag", response_model=TaskDetail)
def drag_task(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    task_id: int,
    request: TaskDragRequest,
) -> TaskDetail:
    """Drag a task to a new column."""
    return task_service.drag_task(session, task_id, user_id, request)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    task_id: int,
) -> None:
    """Soft-delete a task and cascade to sub-tasks/comments."""
    task_service.delete_task(session, task_id, user_id)


@router.get("/{task_id}/comments", response_model=TaskCommentListResponse)
def list_comments(
    session: SessionDep,
    task_id: int,
    page_cursor: Annotated[str | None, Query()] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TaskCommentListResponse:
    """List comments on a task."""
    return task_service.list_task_comments(session, task_id, page_cursor, page_size)


@router.post("/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    task_id: int,
    request: TaskCommentCreateRequest,
) -> TaskCommentResponse:
    """Create a comment on a task."""
    return task_service.create_task_comment(session, task_id, user_id, request)


@comments_router.put("/{comment_id}", response_model=TaskCommentResponse)
def update_comment(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    comment_id: int,
    request: TaskCommentCreateRequest,
) -> TaskCommentResponse:
    """Update a task comment."""
    return task_service.update_task_comment(session, comment_id, user_id, request)


@comments_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    comment_id: int,
) -> None:
    """Delete a task comment."""
    task_service.delete_task_comment(session, comment_id, user_id)
