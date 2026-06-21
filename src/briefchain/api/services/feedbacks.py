"""Business logic service for feedback operations."""

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from briefchain.api.exceptions import APIError
from briefchain.api.schemas.feedbacks import (
    FeedbackCreateRequest,
    FeedbackDetail,
    FeedbackListItem,
    UserRef,
)
from briefchain.models import Brief, Feedback, User
from briefchain.models.enums import FeedbackType


def _format_time(value) -> str:
    return value.isoformat()


def _load_user_map(session: Session, user_ids: set[UUID]) -> dict[UUID, User]:
    if not user_ids:
        return {}
    users = session.execute(select(User).where(User.id.in_(list(user_ids)))).scalars().all()
    return {user.id: user for user in users}


def _require_participant(brief: Brief, user_id: UUID) -> None:
    if brief.created_by != user_id and brief.assigned_to != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only participants can perform this action",
            status_code=403,
        )


def create_feedback(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: FeedbackCreateRequest,
) -> FeedbackDetail:
    """Create feedback on a brief."""
    brief = session.get(Brief, brief_id)
    if brief is None:
        raise APIError(
            code="BRIEF_NOT_FOUND",
            message="Brief not found",
            status_code=404,
        )
    _require_participant(brief, user_id)

    feedback = Feedback(
        id=uuid4(),
        brief_id=brief_id,
        brief_version=brief.current_version,
        type=request.type,
        content=request.content,
        attachments=request.attachments,
        from_user=user_id,
        is_auto_generated=False,
        confirmed_at=None,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)

    users = _load_user_map(session, {feedback.from_user})
    return FeedbackDetail(
        id=feedback.id,
        type=feedback.type,
        from_user=UserRef(id=feedback.from_user, name=users[feedback.from_user].name),
        created_at=_format_time(feedback.created_at),
        brief_id=feedback.brief_id,
        brief_version=feedback.brief_version,
        content=feedback.content,
        attachments=feedback.attachments,
        confirmed_at=None,
    )


def list_feedbacks(
    session: Session,
    brief_id: UUID,
    feedback_type: FeedbackType | None = None,
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
    stmt = stmt.order_by(Feedback.created_at.desc())

    feedbacks = session.execute(stmt).scalars().all()
    user_ids = {feedback.from_user for feedback in feedbacks}
    users = _load_user_map(session, user_ids)

    return [
        FeedbackListItem(
            id=feedback.id,
            type=feedback.type,
            from_user=UserRef(
                id=feedback.from_user,
                name=users.get(feedback.from_user).name if feedback.from_user in users else "",
            ),
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

    users = _load_user_map(session, {feedback.from_user})
    return FeedbackDetail(
        id=feedback.id,
        type=feedback.type,
        from_user=UserRef(
            id=feedback.from_user,
            name=users.get(feedback.from_user).name if feedback.from_user in users else "",
        ),
        created_at=_format_time(feedback.created_at),
        brief_id=feedback.brief_id,
        brief_version=feedback.brief_version,
        content=feedback.content,
        attachments=feedback.attachments,
        confirmed_at=_format_time(feedback.confirmed_at) if feedback.confirmed_at else None,
    )
