"""Kanban and kanban template routes for the BriefChain API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from briefchain.api.dependencies import CurrentUserIdDep, SessionDep, get_current_user_id
from briefchain.api.schemas.kanban import (
    KanbanBoardResponse,
    KanbanColumnsUpdateRequest,
    KanbanColumnsUpdateResponse,
    KanbanConfig,
    KanbanConfigResponse,
    KanbanCreateRequest,
    KanbanTemplateDetailResponse,
    KanbanTemplateListResponse,
    KanbanUpdateRequest,
)
from briefchain.api.services import kanban as kanban_service
from briefchain.models.enums import KanbanGroup

board_router = APIRouter(
    prefix="/kanban",
    tags=["kanban-board"],
    dependencies=[Depends(get_current_user_id)],
)

kanban_router = APIRouter(
    prefix="/kanbans",
    tags=["kanban-config"],
    dependencies=[Depends(get_current_user_id)],
)

template_router = APIRouter(
    prefix="/kanban-templates",
    tags=["kanban-templates"],
    dependencies=[Depends(get_current_user_id)],
)


@board_router.get("/personal", response_model=KanbanBoardResponse)
def get_personal_board(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    group: Annotated[KanbanGroup | None, Query()] = None,
) -> KanbanBoardResponse:
    """Return the authenticated user's personal kanban board."""
    return kanban_service.get_personal_kanban_board(session, user_id, group_override=group)


@kanban_router.post("", response_model=KanbanConfig, status_code=201)
def create_kanban(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    request: KanbanCreateRequest,
) -> KanbanConfig:
    """Create a new kanban board (MVP: personal fallback)."""
    return kanban_service.create_kanban(session, user_id, request)


@kanban_router.get("/{kanban_id}", response_model=KanbanConfigResponse)
def get_kanban(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    kanban_id: int,
) -> KanbanConfigResponse:
    """Get kanban configuration including template and columns."""
    return kanban_service.get_kanban_config(session, kanban_id, user_id)


@kanban_router.put("/{kanban_id}", response_model=KanbanConfigResponse)
def update_kanban(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    kanban_id: int,
    request: KanbanUpdateRequest,
) -> KanbanConfigResponse:
    """Update kanban-level settings."""
    return kanban_service.update_kanban_config(session, kanban_id, user_id, request)


@kanban_router.put("/{kanban_id}/columns", response_model=KanbanColumnsUpdateResponse)
def update_kanban_columns(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    kanban_id: int,
    request: KanbanColumnsUpdateRequest,
) -> KanbanColumnsUpdateResponse:
    """Update a kanban's column configuration with template fork logic."""
    return kanban_service.update_kanban_columns(session, kanban_id, user_id, request)


@template_router.get("", response_model=KanbanTemplateListResponse)
def list_templates(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    page_cursor: Annotated[str | None, Query()] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> KanbanTemplateListResponse:
    """List public and own private kanban templates."""
    return kanban_service.list_kanban_templates(session, user_id, page_cursor, page_size)


@template_router.get("/{template_id}", response_model=KanbanTemplateDetailResponse)
def get_template(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    template_id: int,
) -> KanbanTemplateDetailResponse:
    """Get a kanban template and its columns."""
    return kanban_service.get_kanban_template_detail(session, template_id, user_id)
