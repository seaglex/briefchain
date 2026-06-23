"""Brief routes for the BriefChain API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from briefchain.api.dependencies import CurrentUserIdDep, SessionDep
from briefchain.api.schemas.briefs import (
    BriefCreateRequest,
    BriefDetail,
    BriefLifecycleResponse,
    BriefUpdateRequest,
    SendBriefRequest,
)
from briefchain.api.services import briefs as brief_service
from briefchain.models.enums import BriefStatus

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.post("", response_model=BriefDetail, status_code=status.HTTP_201_CREATED)
def create_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    request: BriefCreateRequest,
) -> BriefDetail:
    """Create a new brief."""
    return brief_service.create_brief(session, user_id, request)


@router.get("")
def list_briefs(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    role: Annotated[str, Query(pattern="^(created|assigned|all)$")] = "all",
    status: Annotated[BriefStatus | None, Query()] = None,
    root_id: Annotated[UUID | None, Query()] = None,
    page_cursor: Annotated[str | None, Query()] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """List briefs with optional filters and cursor pagination."""
    return brief_service.list_briefs(
        session,
        user_id,
        role=role,
        status=status,
        root_id=root_id,
        page_cursor=page_cursor,
        page_size=page_size,
    )


@router.get("/{brief_id}", response_model=BriefDetail)
def get_brief(
    session: SessionDep,
    brief_id: UUID,
) -> BriefDetail:
    """Get a brief with its latest version content."""
    return brief_service.get_brief_detail(session, brief_id)


@router.patch("/{brief_id}", response_model=BriefDetail)
def update_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    request: BriefUpdateRequest,
) -> BriefDetail:
    """Update a draft brief."""
    return brief_service.update_brief(session, brief_id, user_id, request)


@router.post("/{brief_id}/submit", response_model=BriefDetail)
def submit_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
) -> BriefDetail:
    """Submit a draft brief for review."""
    return brief_service.submit_brief(session, brief_id, user_id)


class RejectBriefRequest(BaseModel):
    """Request body for rejecting a brief."""

    reason: str = Field(..., min_length=1)


@router.post("/{brief_id}/send", response_model=BriefLifecycleResponse)
def send_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    request: SendBriefRequest,
) -> BriefLifecycleResponse:
    """Send a reviewed brief to a downstream user or external recipient."""
    return brief_service.send_brief(session, brief_id, user_id, request)


@router.post("/{brief_id}/accept", response_model=BriefLifecycleResponse)
def accept_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
) -> BriefLifecycleResponse:
    """Accept a sent brief."""
    return brief_service.accept_brief(session, brief_id, user_id)


@router.post("/{brief_id}/reject", response_model=BriefLifecycleResponse)
def reject_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    request: RejectBriefRequest,
) -> BriefLifecycleResponse:
    """Reject a sent brief."""
    return brief_service.reject_brief(session, brief_id, user_id, request.reason)


@router.post("/{brief_id}/cancel", response_model=BriefDetail)
def cancel_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
) -> BriefDetail:
    """Cancel a brief."""
    return brief_service.cancel_brief(session, brief_id, user_id)


@router.post("/{brief_id}/complete", response_model=BriefDetail)
def complete_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
) -> BriefDetail:
    """Mark an accepted brief as done."""
    return brief_service.complete_brief(session, brief_id, user_id)
