"""Business logic service for kanban board and template operations."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from briefchain.api.exceptions import APIError
from briefchain.api.schemas.kanban import (
    KanbanBoardResponse,
    KanbanColumnResponse,
    KanbanColumnsUpdateRequest,
    KanbanColumnsUpdateResponse,
    KanbanConfig,
    KanbanConfigResponse,
    KanbanCreateRequest,
    KanbanSummary,
    KanbanSwimlaneResponse,
    KanbanTemplateColumnResponse,
    KanbanTemplateDetailResponse,
    KanbanTemplateListItem,
    KanbanTemplateListResponse,
    KanbanTemplateSummary,
    KanbanUpdateRequest,
)
from briefchain.api.services.tasks import _serialize_task
from briefchain.models import (
    Kanban,
    KanbanGroup,
    KanbanOwnerType,
    KanbanTemplate,
    KanbanTemplateColumn,
    KanbanTemplateMode,
    Task,
    TaskStatus,
    TaskType,
    User,
)


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


def _template_creator_name(session: Session, created_by: UUID) -> str:
    if created_by == SYSTEM_USER_ID:
        return "系统"
    user = session.get(User, created_by)
    return user.name if user else "未知用户"


def _require_owned_kanban(kanban: Kanban, user_id: UUID) -> None:
    if kanban.owner_type == KanbanOwnerType.USER and kanban.owner_id != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="You do not have access to this kanban",
            status_code=403,
        )
    # MVP: team ownership validation is deferred until team membership is implemented.
    if kanban.owner_type == KanbanOwnerType.TEAM:
        raise APIError(
            code="FORBIDDEN",
            message="Team kanbans are not supported in MVP",
            status_code=403,
        )


def _serialize_kanban_summary(kanban: Kanban) -> KanbanSummary:
    return KanbanSummary(
        kanban_id=kanban.kanban_id,
        kanban_template_id=kanban.kanban_template_id,
        kanban_template_mode=kanban.kanban_template_mode,
        group=kanban.group,
        done_visible_days=kanban.done_visible_days,
        is_default=kanban.is_default,
    )


def _serialize_kanban_config(kanban: Kanban) -> KanbanConfig:
    return KanbanConfig(
        kanban_id=kanban.kanban_id,
        kanban_template_id=kanban.kanban_template_id,
        name=kanban.name,
        owner_type=kanban.owner_type,
        owner_id=kanban.owner_id,
        group=kanban.group,
        done_visible_days=kanban.done_visible_days,
        is_default=kanban.is_default,
        created_at=kanban.created_at,
        updated_at=kanban.updated_at,
    )


def _serialize_column(column: KanbanTemplateColumn) -> KanbanTemplateColumnResponse:
    return KanbanTemplateColumnResponse(
        column_id=column.column_id,
        status_key=column.status_key,
        name=column.name,
        color=column.color,
        is_hidden=column.is_hidden,
        position=column.position,
    )


def _serialize_template_summary(template: KanbanTemplate) -> KanbanTemplateSummary:
    return KanbanTemplateSummary(
        kanban_template_id=template.kanban_template_id,
        name=template.name,
        kanban_template_mode=template.kanban_template_mode,
        created_by=template.created_by,
    )


# ---------------------------------------------------------------------------
# Board query
# ---------------------------------------------------------------------------


def get_personal_kanban_board(
    session: Session,
    user_id: UUID,
    group_override: KanbanGroup | None = None,
) -> KanbanBoardResponse:
    """Return the authenticated user's default personal kanban board."""
    kanban = (
        session.execute(
            select(Kanban).where(
                Kanban.owner_type == KanbanOwnerType.USER,
                Kanban.owner_id == user_id,
                Kanban.is_default.is_(True),
            )
        )
        .scalars()
        .first()
    )
    if kanban is None:
        raise APIError(
            code="KANBAN_NOT_FOUND",
            message="Default personal kanban not found",
            status_code=404,
        )

    template = session.get(KanbanTemplate, kanban.kanban_template_id)
    if template is None:
        raise APIError(
            code="KANBAN_NOT_FOUND",
            message="Kanban template not found",
            status_code=404,
        )

    columns = [
        col
        for col in template.columns
        if not col.is_hidden
    ]
    columns.sort(key=lambda c: c.position)
    status_keys = [col.status_key for col in columns]

    # Build task query for the board.
    cutoff = _now() - timedelta(days=kanban.done_visible_days)
    conditions = [
        Task.team_id.is_(None),
        Task.is_deleted.is_(False),
        Task.type.in_([TaskType.TASK, TaskType.BUG]),
        Task.status.in_(status_keys),
        or_(
            Task.status != TaskStatus.DONE,
            Task.updated_at >= cutoff,
        ),
    ]

    tasks = session.execute(select(Task).where(and_(*conditions))).scalars().all()
    task_items = [_serialize_task(t, detail=False) for t in tasks]

    group = group_override if group_override is not None else kanban.group

    def swimlane_key(task_item: Any) -> str | None:
        if group == KanbanGroup.NONE:
            return None
        if group == KanbanGroup.ASSIGNEE:
            return task_item.assignee_name
        if group == KanbanGroup.PRIORITY:
            return task_item.priority.value
        if group == KanbanGroup.BRIEF:
            # MVP: brief_id is used as key; brief titles are not loaded here.
            return str(task_item.brief_id) if task_item.brief_id else None
        return None

    columns_response: list[KanbanColumnResponse] = []
    for col in columns:
        col_tasks = [t for t in task_items if t.status.value == col.status_key]
        lanes: dict[str | None, list[Any]] = {}
        for t in col_tasks:
            key = swimlane_key(t)
            lanes.setdefault(key, []).append(t)
        swimlanes = [
            KanbanSwimlaneResponse(swimlane_key=key, tasks=tasks_list)
            for key, tasks_list in lanes.items()
        ]
        columns_response.append(
            KanbanColumnResponse(
                **_serialize_column(col).model_dump(),
                swimlanes=swimlanes,
            )
        )

    return KanbanBoardResponse(
        kanban=_serialize_kanban_summary(kanban),
        columns=columns_response,
    )


# ---------------------------------------------------------------------------
# Kanban config
# ---------------------------------------------------------------------------


def get_kanban_config(session: Session, kanban_id: int, user_id: UUID) -> KanbanConfigResponse:
    """Return kanban configuration including template and columns."""
    kanban = session.get(Kanban, kanban_id)
    if kanban is None:
        raise APIError(
            code="KANBAN_NOT_FOUND",
            message="Kanban not found",
            status_code=404,
        )
    _require_owned_kanban(kanban, user_id)

    template = session.get(KanbanTemplate, kanban.kanban_template_id)
    if template is None:
        raise APIError(
            code="KANBAN_NOT_FOUND",
            message="Kanban template not found",
            status_code=404,
        )

    columns = sorted(template.columns, key=lambda c: c.position)
    return KanbanConfigResponse(
        kanban=_serialize_kanban_config(kanban),
        template=_serialize_template_summary(template),
        columns=[_serialize_column(c) for c in columns],
    )


def update_kanban_config(
    session: Session,
    kanban_id: int,
    user_id: UUID,
    request: KanbanUpdateRequest,
) -> KanbanConfigResponse:
    """Update kanban-level settings."""
    kanban = session.get(Kanban, kanban_id)
    if kanban is None:
        raise APIError(
            code="KANBAN_NOT_FOUND",
            message="Kanban not found",
            status_code=404,
        )
    _require_owned_kanban(kanban, user_id)

    if request.name is not None:
        kanban.name = request.name
    if request.group is not None:
        kanban.group = request.group
    if request.done_visible_days is not None:
        kanban.done_visible_days = request.done_visible_days
    if request.kanban_template_id is not None:
        template = session.get(KanbanTemplate, request.kanban_template_id)
        if template is None:
            raise APIError(
                code="TEMPLATE_NOT_FOUND",
                message="Kanban template not found",
                status_code=404,
            )
        kanban.kanban_template_id = template.kanban_template_id
        kanban.kanban_template_mode = template.kanban_template_mode

    session.commit()
    session.refresh(kanban)
    return get_kanban_config(session, kanban_id, user_id)


def create_kanban(
    session: Session,
    user_id: UUID,
    request: KanbanCreateRequest,
) -> KanbanConfig:
    """Create a new kanban board (MVP: personal fallback only)."""
    if request.owner_type == KanbanOwnerType.USER and request.owner_id != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Can only create a kanban for yourself",
            status_code=403,
        )

    template = session.get(KanbanTemplate, request.kanban_template_id)
    if template is None:
        raise APIError(
            code="TEMPLATE_NOT_FOUND",
            message="Kanban template not found",
            status_code=404,
        )

    name = "My Kanban"
    if request.owner_type == KanbanOwnerType.TEAM:
        name = "Team Kanban"

    kanban = Kanban(
        kanban_template_id=template.kanban_template_id,
        kanban_template_mode=template.kanban_template_mode,
        name=name,
        owner_type=request.owner_type,
        owner_id=request.owner_id,
        group=request.group or KanbanGroup.NONE,
        done_visible_days=request.done_visible_days or 14,
        is_default=request.is_default or False,
    )
    session.add(kanban)
    session.commit()
    session.refresh(kanban)
    return _serialize_kanban_config(kanban)


# ---------------------------------------------------------------------------
# Column management with fork logic
# ---------------------------------------------------------------------------


def update_kanban_columns(
    session: Session,
    kanban_id: int,
    user_id: UUID,
    request: KanbanColumnsUpdateRequest,
) -> KanbanColumnsUpdateResponse:
    """Update a kanban's column configuration, forking the template when needed."""
    kanban = session.get(Kanban, kanban_id)
    if kanban is None:
        raise APIError(
            code="KANBAN_NOT_FOUND",
            message="Kanban not found",
            status_code=404,
        )
    _require_owned_kanban(kanban, user_id)

    current_template = session.get(KanbanTemplate, kanban.kanban_template_id)
    if current_template is None:
        raise APIError(
            code="TEMPLATE_NOT_FOUND",
            message="Current kanban template not found",
            status_code=404,
        )

    # Fork if the user does not own the current template.
    if current_template.created_by != user_id:
        new_template = KanbanTemplate(
            name=request.name or current_template.name,
            kanban_template_mode=request.kanban_template_mode
            or current_template.kanban_template_mode,
            created_by=user_id,
            is_public=request.is_public if request.is_public is not None else False,
        )
        session.add(new_template)
        session.flush()

        for col in current_template.columns:
            new_template.columns.append(
                KanbanTemplateColumn(
                    status_key=col.status_key,
                    name=col.name,
                    color=col.color,
                    is_hidden=col.is_hidden,
                    position=col.position,
                )
            )

        kanban.kanban_template_id = new_template.kanban_template_id
        kanban.kanban_template_mode = new_template.kanban_template_mode
        target_template = new_template
    else:
        target_template = current_template
        if request.name is not None:
            target_template.name = request.name
        if request.kanban_template_mode is not None:
            target_template.kanban_template_mode = request.kanban_template_mode
        if request.is_public is not None:
            target_template.is_public = request.is_public

    target_columns_by_status = {c.status_key: c for c in target_template.columns}
    target_columns_by_id = {c.column_id: c for c in target_template.columns}

    seen_status_keys: set[str] = set()
    for item in request.columns:
        if item.status_key in seen_status_keys:
            raise APIError(
                code="VALIDATION_ERROR",
                message=f"Duplicate status_key in simple mode: {item.status_key}",
                status_code=422,
            )
        seen_status_keys.add(item.status_key)

        existing: KanbanTemplateColumn | None = None
        if item.column_id is not None:
            existing = target_columns_by_id.get(item.column_id)
        if existing is None:
            existing = target_columns_by_status.get(item.status_key)

        if existing is not None:
            # Simple mode: status_key and position are immutable.
            if existing.status_key != item.status_key:
                raise APIError(
                    code="VALIDATION_ERROR",
                    message="status_key cannot be changed in simple mode",
                    status_code=422,
                )
            if existing.position != item.position:
                raise APIError(
                    code="VALIDATION_ERROR",
                    message="position cannot be changed in simple mode",
                    status_code=422,
                )
            existing.name = item.name
            existing.color = item.color
            existing.is_hidden = item.is_hidden
        else:
            # New column.
            session.add(
                KanbanTemplateColumn(
                    kanban_template_id=target_template.kanban_template_id,
                    status_key=item.status_key,
                    name=item.name,
                    color=item.color,
                    is_hidden=item.is_hidden,
                    position=item.position,
                )
            )

    session.commit()
    session.refresh(target_template)
    columns = sorted(target_template.columns, key=lambda c: c.position)
    return KanbanColumnsUpdateResponse(
        kanban=_serialize_kanban_config(kanban),
        columns=[_serialize_column(c) for c in columns],
    )


# ---------------------------------------------------------------------------
# Template listing / preview
# ---------------------------------------------------------------------------


def list_kanban_templates(
    session: Session,
    user_id: UUID,
    page_cursor: str | None = None,
    page_size: int = 20,
) -> KanbanTemplateListResponse:
    """Return public templates and the user's own private templates."""
    page_size = max(1, min(page_size, 100))

    conditions = [
        or_(
            KanbanTemplate.is_public.is_(True),
            KanbanTemplate.created_by == user_id,
        )
    ]

    last_updated_at = None
    last_template_id = None
    if page_cursor:
        try:
            decoded = _decode_cursor(page_cursor)
            last_updated_at = datetime.fromisoformat(decoded["updated_at"])
            last_template_id = decoded["template_id"]
        except (ValueError, KeyError) as exc:
            raise APIError(
                code="INVALID_CURSOR",
                message="Invalid pagination cursor",
                status_code=400,
            ) from exc

    if last_updated_at and last_template_id is not None:
        conditions.append(
            or_(
                KanbanTemplate.updated_at < last_updated_at,
                and_(
                    KanbanTemplate.updated_at == last_updated_at,
                    KanbanTemplate.kanban_template_id < last_template_id,
                ),
            )
        )

    stmt = (
        select(KanbanTemplate)
        .where(and_(*conditions))
        .order_by(KanbanTemplate.updated_at.desc(), KanbanTemplate.kanban_template_id.desc())
        .limit(page_size)
    )
    templates = session.execute(stmt).scalars().all()

    items = [
        KanbanTemplateListItem(
            kanban_template_id=t.kanban_template_id,
            name=t.name,
            kanban_template_mode=t.kanban_template_mode,
            created_by=t.created_by,
            created_by_name=_template_creator_name(session, t.created_by),
            is_public=t.is_public,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in templates
    ]

    next_cursor = None
    if len(templates) == page_size:
        last = templates[-1]
        next_cursor = _encode_cursor(
            {
                "updated_at": last.updated_at.isoformat(),
                "template_id": last.kanban_template_id,
            }
        )

    return KanbanTemplateListResponse(templates=items, next_cursor=next_cursor)


def get_kanban_template_detail(
    session: Session,
    template_id: int,
    user_id: UUID,
) -> KanbanTemplateDetailResponse:
    """Return a template and its columns if visible to the user."""
    template = session.get(KanbanTemplate, template_id)
    if template is None:
        raise APIError(
            code="TEMPLATE_NOT_FOUND",
            message="Kanban template not found",
            status_code=404,
        )
    if not template.is_public and template.created_by != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="You do not have access to this template",
            status_code=403,
        )

    columns = sorted(template.columns, key=lambda c: c.position)
    item = KanbanTemplateListItem(
        kanban_template_id=template.kanban_template_id,
        name=template.name,
        kanban_template_mode=template.kanban_template_mode,
        created_by=template.created_by,
        created_by_name=_template_creator_name(session, template.created_by),
        is_public=template.is_public,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )
    return KanbanTemplateDetailResponse(
        template=item,
        columns=[_serialize_column(c) for c in columns],
    )
