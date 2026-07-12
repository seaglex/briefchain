"""Tests for the Arbiter worker."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from briefchain.api.config import settings
from briefchain.arbiter.handlers.review import ReviewHandler, TransientReviewError
from briefchain.arbiter.queue.base import QueueTask
from briefchain.arbiter.skills.schemas import BriefReviewResult
from briefchain.arbiter.worker import ArbiterWorker
from briefchain.models import BriefArbiterReview, BriefVersion
from briefchain.models.enums import ArbiterReviewStatus, BriefVersionStatus


@pytest.fixture(autouse=True)
def skip_review_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure SKIP_REVIEW is disabled so tests exercise the LLM path by default."""
    monkeypatch.setattr(settings, "skip_review", False)


@pytest.fixture
def processing_review(db_session: Session, draft_brief) -> BriefArbiterReview:
    """Create a review in processing state."""
    review = BriefArbiterReview(
        id=uuid4(),
        brief_id=draft_brief.brief_id,
        brief_version=1,
        arbiter_id="async-arbiter-v1",
        status=ArbiterReviewStatus.PROCESSING,
        attempt_count=0,
        webhook_url=None,
    )
    db_session.add(review)
    db_session.commit()
    return review


async def test_review_handler_force_skip(db_session: Session, processing_review) -> None:
    """SKIP_REVIEW=true marks the review force_skipped without LLM call."""
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(settings, "skip_review", True)
    handler = ReviewHandler()

    with db_session.begin():
        await handler.execute(db_session, processing_review)

    assert processing_review.status == ArbiterReviewStatus.FORCE_SKIPPED
    assert processing_review.reviewed_at is not None
    monkeypatch.undo()


async def test_review_handler_passed(
    db_session: Session,
    processing_review,
    draft_brief,
) -> None:
    """ReviewHandler updates review to passed when LLM returns passed."""
    version = db_session.get(BriefVersion, (draft_brief.brief_id, 1))
    version.status = BriefVersionStatus.DRAFT
    version.content = "Clear requirement with Why, What, Goals, Hypothesis."
    db_session.commit()

    llm_client = AsyncMock()
    llm_client.generate_structured.return_value = BriefReviewResult(
        thinking="all good",
        passed=True,
        score=85,
        issues=[],
        suggestions=[],
    )

    handler = ReviewHandler(llm_client=llm_client)

    with db_session.begin():
        await handler.execute(db_session, processing_review)

    assert processing_review.status == ArbiterReviewStatus.PASSED
    assert processing_review.score == 85
    assert processing_review.issues == []
    assert processing_review.reviewed_at is not None


async def test_review_handler_rejected(
    db_session: Session,
    processing_review,
    draft_brief,
) -> None:
    """ReviewHandler updates review to rejected when LLM returns rejected."""
    version = db_session.get(BriefVersion, (draft_brief.brief_id, 1))
    version.status = BriefVersionStatus.DRAFT
    version.content = "Vague requirement."
    db_session.commit()

    llm_client = AsyncMock()
    llm_client.generate_structured.return_value = BriefReviewResult(
        thinking="missing goals",
        passed=False,
        score=45,
        issues=["Goals are not measurable"],
        suggestions=["Add measurable goals"],
    )

    handler = ReviewHandler(llm_client=llm_client)

    with db_session.begin():
        await handler.execute(db_session, processing_review)

    assert processing_review.status == ArbiterReviewStatus.REJECTED
    assert processing_review.score == 45
    assert processing_review.suggestions == ["Add measurable goals"]


async def test_review_handler_transient_error(
    db_session: Session,
    processing_review,
    draft_brief,
) -> None:
    """LLM errors raise TransientReviewError for retry."""
    version = db_session.get(BriefVersion, (draft_brief.brief_id, 1))
    version.status = BriefVersionStatus.DRAFT
    db_session.commit()

    llm_client = AsyncMock()
    llm_client.generate_structured.side_effect = ConnectionError("timeout")

    handler = ReviewHandler(llm_client=llm_client)

    with pytest.raises(TransientReviewError), db_session.begin():
        await handler.execute(db_session, processing_review)


async def test_worker_process_task_success(
    db_session: Session,
    processing_review,
    draft_brief,
) -> None:
    """Worker processes a review task to completion."""
    version = db_session.get(BriefVersion, (draft_brief.brief_id, 1))
    version.status = BriefVersionStatus.DRAFT
    version.content = "Good requirement."
    db_session.commit()

    @contextmanager
    def session_factory():
        yield db_session

    queue = MagicMock()
    llm_client = AsyncMock()
    llm_client.generate_structured.return_value = BriefReviewResult(
        thinking="ok",
        passed=True,
        score=80,
        issues=[],
        suggestions=[],
    )

    worker = ArbiterWorker(
        queue=queue,
        poll_interval=0.01,
        session_factory=session_factory,
    )
    worker._handlers["review"] = ReviewHandler(llm_client=llm_client)

    task = QueueTask(id=uuid4(), type="review", ref_id=processing_review.id)
    await worker._process_task(task)

    db_session.refresh(processing_review)
    assert processing_review.status == ArbiterReviewStatus.PASSED


async def test_worker_unknown_task_type() -> None:
    """Worker logs and skips unknown task types."""
    queue = MagicMock()
    worker = ArbiterWorker(queue=queue)

    task = QueueTask(id=uuid4(), type="summary", ref_id=uuid4())
    # Should not raise.
    await worker._process_task(task)
