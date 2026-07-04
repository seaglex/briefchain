"""Business logic service for task and task comment operations."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from briefchain.api.exceptions import APIError
from briefchain.api.schemas.tasks import (
    TaskCommentCreateRequest,
    TaskCommentListResponse,
    TaskCommentResponse,
    TaskCreateRequest,
    TaskDetail,
    TaskDetailResponse,
    TaskDragRequest,
    TaskListItem,
    TaskListResponse,
    TaskUpdateRequest,
)
from briefchain.models import Task, TaskComment, TaskPriority, TaskStatus, TaskType, User


SYSTEM_USER_ID = UUID(int=0)


def _now() -> datetime:
    return datetime.now(UTC)


def _encode_cursor(data: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")


def _decode_cursor(cursor: str) -> dict[str, Any]:
    padding = 4 - len(cursor) % 4
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * padding).decode())


def _load_user(session: Session, user_id: UUID) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise APIError(
            code="USER_NOT_FOUND",
            message="User not found",
            status_code=404,
        )
    return user


def _require_task(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None or task.is_deleted:
        raise APIError(
            code="TASK_NOT_FOUND",
            message="Task not found",
            status_code=404,
        )
    return task


def _require_creator_or_assignee(task: Task, user_id: UUID) -> None:
    if task.created_by != user_id and task.assignee_id != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only the creator or assignee can perform this action",
            status_code=403,
        )


def _require_creator(task: Task, user_id: UUID) -> None:
    if task.created_by != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only the creator can perform this action",
            status_code=403,
        )


def _set_status_changed(task: Task, user_id: UUID) -> None:
    task.status_changed_by = user_id
    task.status_changed_at = _now()


def _snapshot_assignee(session: Session, task: Task, assignee_id: UUID | None) -> None:
    task.assignee_id = assignee_id
    if assignee_id is not None:
        user = _load_user(session, assignee_id)
        task.assignee_name = user.name
    else:
        task.assignee_name = None


def _serialize_task(task: Task, detail: bool = False) -> TaskListItem:
    base = TaskListItem(
        task_id=task.task_id,
        type=task.type,
        title=task.title,
        status=task.status,
        priority=task.priority,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee_name,
        brief_id=task.brief_id,
        updated_at=task.updated_at,
    )
    if not detail:
        return base
    return TaskDetail(
        **base.model_dump(),
        parent_task_id=task.parent_task_id,
        team_id=task.team_id,
        content=task.content,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        due_date=task.due_date,
        status_changed_by=task.status_changed_by,
        status_changed_at=task.status_changed_at,
        created_by=task.created_by,
        created_by_name=task.created_by_name,
        created_at=task.created_at,
        is_deleted=task.is_deleted,
        deleted_by=task.deleted_by,
        deleted_at=task.deleted_at,
    )


def _serialize_comment(comment: TaskComment) -> TaskCommentResponse:
    return TaskCommentResponse(
        id=comment.id,
        content=comment.content,
        created_by=comment.created_by,
        created_by_name=comment.created_by_name,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def create_task(session: Session, user_id: UUID, request: TaskCreateRequest) -> TaskDetail:
    """Create a new task."""
    creator = _load_user(session, user_id)

    if request.type == TaskType.SUB_TASK and request.parent_task_id is None:
        raise APIError(
            code="INVALID_REQUEST",
            message="parent_task_id is required for sub_task",
            status_code=422,
        )

    now = _now()
    task = Task(
        brief_id=request.brief_id,
        parent_task_id=request.parent_task_id,
        team_id=request.team_id,
        type=request.type,
        title=request.title,
        content=request.content,
        status=request.status or TaskStatus.TODO,
        priority=request.priority or TaskPriority.P2,
        created_by=user_id,
        created_by_name=creator.name,
        assignee_id=None,
        assignee_name=None,
        estimated_hours=request.estimated_hours,
        due_date=request.due_date,
        status_changed_by=None,
        status_changed_at=None,
        is_deleted=False,
        deleted_by=None,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )

    if request.assignee_id is not None:
        _snapshot_assignee(session, task, request.assignee_id)

    if request.status is not None:
        _set_status_changed(task, user_id)

    session.add(task)
    session.commit()
    session.refresh(task)
    return _serialize_task(task, detail=True)


def list_tasks(
    session: Session,
    user_id: UUID,
    brief_id: UUID | None = None,
    task_type: TaskType | None = None,
    status: TaskStatus | None = None,
    team_id: UUID | None = None,
    assignee_id: UUID | None = None,
    priority: TaskPriority | None = None,
    page_cursor: str | None = None,
    page_size: int = 20,
) -> TaskListResponse:
    """Return a paginated list of tasks visible to the user."""
    page_size = max(1, min(page_size, 100))

    conditions = [Task.is_deleted.is_(False)]
    if team_id is not None:
        conditions.append(Task.team_id == team_id)
    else:
        # Personal scope: tasks without a team that the user owns or is assigned to.
        conditions.append(
            and_(
                Task.team_id.is_(None),
                or_(
                    Task.created_by == user_id,
                    Task.assignee_id == user_id,
                ),
            )
        )

    if brief_id is not None:
        conditions.append(Task.brief_id == brief_id)
    if task_type is not None:
        conditions.append(Task.type == task_type)
    if status is not None:
        conditions.append(Task.status == status)
    if assignee_id is not None:
        conditions.append(Task.assignee_id == assignee_id)
    if priority is not None:
        conditions.append(Task.priority == priority)

    last_updated_at = None
    last_task_id = None
    if page_cursor:
        try:
            decoded = _decode_cursor(page_cursor)
            last_updated_at = datetime.fromisoformat(decoded["updated_at"])
            last_task_id = decoded["task_id"]
        except (ValueError, KeyError) as exc:
            raise APIError(
                code="INVALID_CURSOR",
                message="Invalid pagination cursor",
                status_code=400,
            ) from exc

    if last_updated_at and last_task_id is not None:
        conditions.append(
            or_(
                Task.updated_at < last_updated_at,
                and_(
                    Task.updated_at == last_updated_at,
                    Task.task_id < last_task_id,
                ),
            )
        )

    stmt = (
        select(Task)
        .where(and_(True, *conditions))
        .order_by(Task.updated_at.desc(), Task.task_id.desc())
        .limit(page_size)
    )
    tasks = session.execute(stmt).scalars().all()

    items = [_serialize_task(task, detail=False) for task in tasks]

    next_cursor = None
    if len(tasks) == page_size:
        last = tasks[-1]
        next_cursor = _encode_cursor(
            {
                "updated_at": last.updated_at.isoformat(),
                "task_id": last.task_id,
            }
        )

    return TaskListResponse(tasks=items, next_cursor=next_cursor)


def get_task_detail(session: Session, task_id: int) -> TaskDetailResponse:
    """Return task detail with sub-tasks and latest comments."""
    task = _require_task(session, task_id)
    sub_tasks = (
        session.execute(
            select(Task)
            .where(Task.parent_task_id == task_id, Task.is_deleted.is_(False))
            .order_by(Task.updated_at.desc())
        )
        .scalars()
        .all()
    )
    comments = task.comments[:5]
    return TaskDetailResponse(
        task=_serialize_task(task, detail=True),
        sub_tasks=[_serialize_task(t, detail=False) for t in sub_tasks],
        comments=[_serialize_comment(c) for c in comments],
    )


def update_task(
    session: Session,
    task_id: int,
    user_id: UUID,
    request: TaskUpdateRequest,
) -> TaskDetail:
    """Update editable task fields."""
    task = _require_task(session, task_id)
    _require_creator_or_assignee(task, user_id)

    if request.title is not None:
        task.title = request.title
    if request.content is not None:
        task.content = request.content
    if request.priority is not None:
        task.priority = request.priority
    if request.estimated_hours is not None:
        task.estimated_hours = request.estimated_hours
    if request.actual_hours is not None:
        task.actual_hours = request.actual_hours
    if request.due_date is not None:
        task.due_date = request.due_date

    if request.status is not None and task.status != request.status:
        task.status = request.status
        _set_status_changed(task, user_id)

    if request.assignee_id is not None and task.assignee_id != request.assignee_id:
        _snapshot_assignee(session, task, request.assignee_id)
        # Clearing assignee explicitly is not supported here; use empty string? None stays.

    session.commit()
    session.refresh(task)
    return _serialize_task(task, detail=True)


def drag_task(
    session: Session,
    task_id: int,
    user_id: UUID,
    request: TaskDragRequest,
) -> TaskDetail:
    """Drag a task to a new column/status."""
    task = _require_task(session, task_id)
    _require_creator_or_assignee(task, user_id)

    if task.status != request.status:
        task.status = request.status
        _set_status_changed(task, user_id)

    if request.assignee_id is not None and task.assignee_id != request.assignee_id:
        _snapshot_assignee(session, task, request.assignee_id)

    session.commit()
    session.refresh(task)
    return _serialize_task(task, detail=True)


def delete_task(session: Session, task_id: int, user_id: UUID) -> None:
    """Soft-delete a task and cascade to sub-tasks and comments."""
    task = _require_task(session, task_id)
    _require_creator(task, user_id)

    now = _now()
    task.is_deleted = True
    task.deleted_at = now
    task.deleted_by = user_id

    sub_tasks = (
        session.execute(select(Task).where(Task.parent_task_id == task_id))
        .scalars()
        .all()
    )
    for sub in sub_tasks:
        sub.is_deleted = True
        sub.deleted_at = now
        sub.deleted_by = user_id

    comments = (
        session.execute(select(TaskComment).where(TaskComment.task_id == task_id))
        .scalars()
        .all()
    )
    for comment in comments:
        session.delete(comment)

    session.commit()


# ---------------------------------------------------------------------------
# Task comments
# ---------------------------------------------------------------------------


def list_task_comments(
    session: Session,
    task_id: int,
    page_cursor: str | None = None,
    page_size: int = 20,
) -> TaskCommentListResponse:
    """Return a paginated list of comments for a task."""
    task = _require_task(session, task_id)
    page_size = max(1, min(page_size, 100))

    conditions = [TaskComment.task_id == task_id]

    last_created_at = None
    last_comment_id = None
    if page_cursor:
        try:
            decoded = _decode_cursor(page_cursor)
            last_created_at = datetime.fromisoformat(decoded["created_at"])
            last_comment_id = decoded["comment_id"]
        except (ValueError, KeyError) as exc:
            raise APIError(
                code="INVALID_CURSOR",
                message="Invalid pagination cursor",
                status_code=400,
            ) from exc

    if last_created_at and last_comment_id is not None:
        conditions.append(
            or_(
                TaskComment.created_at < last_created_at,
                and_(
                    TaskComment.created_at == last_created_at,
                    TaskComment.id < last_comment_id,
                ),
            )
        )

    stmt = (
        select(TaskComment)
        .where(and_(True, *conditions))
        .order_by(TaskComment.created_at.desc(), TaskComment.id.desc())
        .limit(page_size)
    )
    comments = session.execute(stmt).scalars().all()

    items = [_serialize_comment(c) for c in comments]

    next_cursor = None
    if len(comments) == page_size:
        last = comments[-1]
        next_cursor = _encode_cursor(
            {
                "created_at": last.created_at.isoformat(),
                "comment_id": last.id,
            }
        )

    return TaskCommentListResponse(comments=items, next_cursor=next_cursor)


def create_task_comment(
    session: Session,
    task_id: int,
    user_id: UUID,
    request: TaskCommentCreateRequest,
) -> TaskCommentResponse:
    """Create a comment on a task."""
    task = _require_task(session, task_id)
    creator = _load_user(session, user_id)

    comment = TaskComment(
        task_id=task.task_id,
        content=request.content,
        created_by=user_id,
        created_by_name=creator.name,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return _serialize_comment(comment)


def update_task_comment(
    session: Session,
    comment_id: int,
    user_id: UUID,
    request: TaskCommentCreateRequest,
) -> TaskCommentResponse:
    """Update a task comment."""
    comment = session.get(TaskComment, comment_id)
    if comment is None:
        raise APIError(
            code="COMMENT_NOT_FOUND",
            message="Comment not found",
            status_code=404,
        )
    if comment.created_by != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only the creator can update this comment",
            status_code=403,
        )

    comment.content = request.content
    session.commit()
    session.refresh(comment)
    return _serialize_comment(comment)


def delete_task_comment(session: Session, comment_id: int, user_id: UUID) -> None:
    """Delete a task comment."""
    comment = session.get(TaskComment, comment_id)
    if comment is None:
        raise APIError(
            code="COMMENT_NOT_FOUND",
            message="Comment not found",
            status_code=404,
        )
    if comment.created_by != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only the creator can delete this comment",
            status_code=403,
        )

    session.delete(comment)
    session.commit()
