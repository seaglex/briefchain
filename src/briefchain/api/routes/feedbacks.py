"""Feedback routes for the BriefChain API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from briefchain.api.dependencies import SessionDep
from briefchain.api.schemas.feedbacks import FeedbackDetail, FeedbackListItem
from briefchain.api.services import feedbacks as feedback_service

brief_router = APIRouter(prefix="/briefs", tags=["brief-feedbacks"])
feedback_router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


@brief_router.get("/{brief_id}/feedbacks", response_model=list[FeedbackListItem])
def list_feedbacks(
    session: SessionDep,
    brief_id: UUID,
    feedback_type: Annotated[str | None, Query()] = None,
    is_to_down: Annotated[bool | None, Query()] = None,
) -> list[FeedbackListItem]:
    """List feedbacks for a brief."""
    return feedback_service.list_feedbacks(session, brief_id, feedback_type, is_to_down)


@feedback_router.get("/{feedback_id}", response_model=FeedbackDetail)
def get_feedback(
    session: SessionDep,
    feedback_id: UUID,
) -> FeedbackDetail:
    """Get a single feedback detail."""
    return feedback_service.get_feedback(session, feedback_id)
