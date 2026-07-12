"""Review routes for the BriefChain API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from briefchain.api.dependencies import CurrentUserIdDep, SessionDep, get_current_user_id
from briefchain.api.schemas.reviews import (
    ReviewAcceptedResponse,
    ReviewCreateRequest,
    ReviewResponse,
)
from briefchain.api.services import reviews as review_service

router = APIRouter(
    prefix="/briefs",
    tags=["reviews"],
    dependencies=[Depends(get_current_user_id)],
)


@router.post(
    "/{brief_id}/reviews",
    response_model=ReviewAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_review(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    request: ReviewCreateRequest,
) -> ReviewAcceptedResponse:
    """Trigger an asynchronous Arbiter review for a brief."""
    return review_service.create_review(session, brief_id, user_id, request)


@router.get("/{brief_id}/reviews/{review_id}", response_model=ReviewResponse)
def get_review(
    session: SessionDep,
    brief_id: UUID,
    review_id: UUID,
) -> ReviewResponse:
    """Get the status and results of a review."""
    return review_service.get_review(session, brief_id, review_id)
