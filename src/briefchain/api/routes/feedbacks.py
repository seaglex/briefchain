"""Feedback routes for the BriefChain API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from briefchain.api.dependencies import CurrentUserIdDep, SessionDep
from briefchain.api.schemas.feedbacks import (
    FeedbackCreateRequest,
    FeedbackDetail,
    FeedbackListItem,
)
from briefchain.api.services import feedbacks as feedback_service
from briefchain.models.enums import FeedbackType

brief_router = APIRouter(prefix="/briefs", tags=["brief-feedbacks"])
feedback_router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


@brief_router.post(
    "/{brief_id}/feedbacks",
    response_model=FeedbackDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_feedback(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    request: FeedbackCreateRequest,
) -> FeedbackDetail:
    """Create feedback on a brief."""
    return feedback_service.create_feedback(session, brief_id, user_id, request)


@brief_router.get("/{brief_id}/feedbacks")
def list_feedbacks(
    session: SessionDep,
    brief_id: UUID,
    feedback_type: Annotated[FeedbackType | None, Query()] = None,
) -> list[FeedbackListItem]:
    """List feedbacks for a brief."""
    return feedback_service.list_feedbacks(session, brief_id, feedback_type)


@feedback_router.get("/{feedback_id}", response_model=FeedbackDetail)
def get_feedback(
    session: SessionDep,
    feedback_id: UUID,
) -> FeedbackDetail:
    """Get a single feedback detail."""
    return feedback_service.get_feedback(session, feedback_id)
