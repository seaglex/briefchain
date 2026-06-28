"""Business logic service for feedback operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from briefchain.api.exceptions import APIError
from briefchain.api.schemas.feedbacks import FeedbackDetail, FeedbackListItem
from briefchain.models import Brief, Feedback


def _format_time(value) -> str:
    return value.isoformat()


def list_feedbacks(
    session: Session,
    brief_id: UUID,
    feedback_type: str | None = None,
    is_to_down: bool | None = None,
) -> list[FeedbackListItem]:
    """List feedbacks for a brief."""
    brief = session.get(Brief, brief_id)
    if brief is None:
        raise APIError(
            code="BRIEF_NOT_FOUND",
            message="Brief not found",
            status_code=404,
        )

    stmt = select(Feedback).where(Feedback.brief_id == brief_id)
    if feedback_type is not None:
        stmt = stmt.where(Feedback.type == feedback_type)
    if is_to_down is not None:
        stmt = stmt.where(Feedback.is_to_down == is_to_down)
    stmt = stmt.order_by(Feedback.created_at.desc())

    feedbacks = session.execute(stmt).scalars().all()

    return [
        FeedbackListItem(
            id=feedback.id,
            brief_id=feedback.brief_id,
            brief_version=feedback.brief_version,
            is_to_down=feedback.is_to_down,
            type=feedback.type,
            from_user_id=feedback.from_user,
            from_user_name=feedback.from_user_name,
            to_user_id=feedback.to_user,
            to_user_name=feedback.to_user_name,
            content=feedback.content,
            created_at=_format_time(feedback.created_at),
        )
        for feedback in feedbacks
    ]


def get_feedback(session: Session, feedback_id: UUID) -> FeedbackDetail:
    """Get a single feedback detail."""
    feedback = session.get(Feedback, feedback_id)
    if feedback is None:
        raise APIError(
            code="FEEDBACK_NOT_FOUND",
            message="Feedback not found",
            status_code=404,
        )

    return FeedbackDetail(
        id=feedback.id,
        brief_id=feedback.brief_id,
        brief_version=feedback.brief_version,
        is_to_down=feedback.is_to_down,
        type=feedback.type,
        from_user_id=feedback.from_user,
        from_user_name=feedback.from_user_name,
        to_user_id=feedback.to_user,
        to_user_name=feedback.to_user_name,
        content=feedback.content,
        attachments=feedback.attachments,
        is_auto_generated=feedback.is_auto_generated,
        confirmed_at=_format_time(feedback.confirmed_at) if feedback.confirmed_at else None,
        created_at=_format_time(feedback.created_at),
    )
