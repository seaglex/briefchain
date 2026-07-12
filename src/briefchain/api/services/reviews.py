"""Business logic for Arbiter review API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from briefchain.api.config import settings
from briefchain.api.exceptions import APIError
from briefchain.api.schemas.reviews import (
    ReviewAcceptedResponse,
    ReviewCreateRequest,
    ReviewResponse,
)
from briefchain.arbiter.queue.factory import create_queue
from briefchain.models import Brief, BriefArbiterReview, BriefVersion
from briefchain.models.enums import ArbiterReviewStatus, BriefVersionStatus


def _now() -> datetime:
    return datetime.now(UTC)


def _require_brief(session: Session, brief_id: UUID) -> Brief:
    brief = session.get(Brief, brief_id)
    if brief is None:
        raise APIError(
            code="BRIEF_NOT_FOUND",
            message="Brief not found",
            status_code=404,
        )
    return brief


def _require_creator(brief: Brief, user_id: UUID) -> None:
    if brief.created_by != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only the creator can perform this action",
            status_code=403,
        )


def _latest_unfinalized_version(brief: Brief) -> BriefVersion | None:
    """Return the most recent unfinalized version (draft or reviewed), if any."""
    for version in reversed(brief.versions):
        if version.status in {BriefVersionStatus.DRAFT, BriefVersionStatus.REVIEWED}:
            return version
    return None


def _has_processing_review(session: Session, brief_id: UUID) -> bool:
    """Return True if the brief already has a processing review."""
    review = session.execute(
        select(BriefArbiterReview).where(
            BriefArbiterReview.brief_id == brief_id,
            BriefArbiterReview.status == ArbiterReviewStatus.PROCESSING,
        )
    ).scalars().first()
    return review is not None


def _get_existing_processing_review(
    session: Session,
    brief_id: UUID,
) -> BriefArbiterReview | None:
    """Return the existing processing review for a brief, if any."""
    return session.execute(
        select(BriefArbiterReview).where(
            BriefArbiterReview.brief_id == brief_id,
            BriefArbiterReview.status == ArbiterReviewStatus.PROCESSING,
        )
    ).scalars().first()


def _serialize_review_response(review: BriefArbiterReview) -> ReviewResponse:
    return ReviewResponse(
        review_id=review.id,
        brief_id=review.brief_id,
        brief_version=review.brief_version,
        status=review.status,
        attempt_count=review.attempt_count,
        created_at=review.created_at,
        arbiter_id=review.arbiter_id,
        score=review.score,
        issues=review.issues,
        suggestions=review.suggestions,
        error=review.error,
        reviewed_at=review.reviewed_at,
    )


def create_review(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: ReviewCreateRequest,
) -> ReviewAcceptedResponse:
    """Create an asynchronous review for the latest editable brief version."""
    from briefchain.api.services.briefs import _load_brief_with_versions

    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)

    existing = _get_existing_processing_review(session, brief_id)
    if existing is not None:
        raise APIError(
            code="REVIEW_ALREADY_IN_PROGRESS",
            message="A review for this brief is already in progress",
            status_code=409,
            details={"existing_review_id": str(existing.id)},
        )

    version = _latest_unfinalized_version(brief)
    if version is None:
        raise APIError(
            code="NO_EDITABLE_VERSION",
            message="No editable version available for review",
            status_code=409,
        )

    review = BriefArbiterReview(
        id=uuid4(),
        brief_id=brief.brief_id,
        brief_version=version.version,
        arbiter_id="async-arbiter-v1",
        status=ArbiterReviewStatus.PROCESSING,
        attempt_count=0,
        webhook_url=request.webhook_url or settings.arbiter_webhook_url,
        issues=[],
        suggestions=[],
    )
    session.add(review)
    session.flush()

    queue = create_queue()
    queue.enqueue(session, "review", review.id)

    session.commit()
    session.refresh(review)

    return ReviewAcceptedResponse(
        review_id=review.id,
        brief_id=review.brief_id,
        brief_version=review.brief_version,
        status=review.status,
        created_at=review.created_at,
    )


def get_review(session: Session, brief_id: UUID, review_id: UUID) -> ReviewResponse:
    """Return a review by ID, verifying it belongs to the given brief."""
    review = session.get(BriefArbiterReview, review_id)
    if review is None or review.brief_id != brief_id:
        raise APIError(
            code="REVIEW_NOT_FOUND",
            message="Review not found",
            status_code=404,
        )
    return _serialize_review_response(review)


def get_latest_review(session: Session, brief_id: UUID) -> BriefArbiterReview | None:
    """Return the most recent review for a brief."""
    return session.execute(
        select(BriefArbiterReview)
        .where(BriefArbiterReview.brief_id == brief_id)
        .order_by(BriefArbiterReview.created_at.desc())
    ).scalars().first()
