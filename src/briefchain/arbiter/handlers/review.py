"""Handlers for Arbiter task types."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from briefchain.api.config import settings
from briefchain.arbiter.llm.client import LLMClient, LLMConfigurationError
from briefchain.arbiter.skills.loader import load_brief_review_skill
from briefchain.arbiter.skills.schemas import BriefReviewResult
from briefchain.arbiter.webhook import notify_review_completed
from briefchain.models import BriefArbiterReview, BriefVersion
from briefchain.models.enums import ArbiterReviewStatus, BriefVersionStatus

logger = logging.getLogger(__name__)


class TransientReviewError(Exception):
    """Raised when a review fails due to a transient LLM or network error."""


class ReviewHandler:
    """Handler for ``type="review"`` tasks."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """Initialize the handler with an optional LLM client override."""
        self._llm_client = llm_client

    async def execute(self, session: Session, review: BriefArbiterReview) -> None:
        """Execute the review task and update the review record.

        Args:
            session: SQLAlchemy session within an active transaction.
            review: The review record to process.

        Raises:
            TransientReviewError: When the LLM call fails transiently.
        """
        if settings.skip_review:
            await self._force_skip(session, review)
            return

        version = self._load_version(session, review)
        skill = load_brief_review_skill()

        client = self._llm_client
        if client is None:
            client = LLMClient()

        try:
            result = await client.generate_structured(
                system_prompt=skill.instructions,
                user_content=version.content,
                output_schema=BriefReviewResult,
            )
        except LLMConfigurationError as exc:
            # Configuration errors should not be retried indefinitely.
            logger.error("LLM configuration error for review %s: %s", review.id, exc)
            self._mark_failed(session, review, str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("Transient LLM error for review %s: %s", review.id, exc)
            raise TransientReviewError(str(exc)) from exc

        if result.passed:
            review.status = ArbiterReviewStatus.PASSED
        else:
            review.status = ArbiterReviewStatus.REJECTED
        review.score = result.score
        review.issues = [{"text": issue} for issue in result.issues]
        review.suggestions = result.suggestions
        review.reviewed_at = datetime.now(UTC)
        review.error = None

        # Mark the reviewed version as ready to send.
        version = self._load_version(session, review)
        if version.status == BriefVersionStatus.DRAFT:
            version.status = BriefVersionStatus.REVIEWED
            version.arbiter_review_id = review.id

    async def _force_skip(self, session: Session, review: BriefArbiterReview) -> None:
        """Mark the review as force-skipped without calling the LLM."""
        review.status = ArbiterReviewStatus.FORCE_SKIPPED
        review.score = None
        review.issues = []
        review.suggestions = []
        review.reviewed_at = datetime.now(UTC)
        review.error = None

        # Treat force-skipped the same as passed for version lifecycle.
        version = self._load_version(session, review)
        if version.status == BriefVersionStatus.DRAFT:
            version.status = BriefVersionStatus.REVIEWED
            version.arbiter_review_id = review.id

    def _load_version(self, session: Session, review: BriefArbiterReview) -> BriefVersion:
        """Load the brief version associated with the review."""
        version = session.get(BriefVersion, (review.brief_id, review.brief_version))
        if version is None:
            raise TransientReviewError(
                f"Brief version {review.brief_version} not found for brief {review.brief_id}"
            )
        return version

    def _mark_failed(self, session: Session, review: BriefArbiterReview, error: str) -> None:
        """Mark the review as failed due to a non-retryable error."""
        review.status = ArbiterReviewStatus.FAILED
        review.error = error
        review.reviewed_at = datetime.now(UTC)


async def notify_terminal_state(review: BriefArbiterReview) -> None:
    """Send a webhook notification for a review that reached a terminal state."""
    await notify_review_completed(
        review_id=review.id,
        brief_id=review.brief_id,
        status=review.status,
        score=review.score,
        webhook_url=review.webhook_url,
        error=review.error,
    )
