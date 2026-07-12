"""Webhook notification sender for Arbiter review events."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

import httpx

from briefchain.api.config import settings
from briefchain.models.enums import ArbiterReviewStatus

logger = logging.getLogger(__name__)


async def notify_review_completed(
    review_id: UUID,
    brief_id: UUID,
    status: ArbiterReviewStatus,
    score: int | None,
    webhook_url: str | None,
    error: str | None = None,
) -> None:
    """Send a webhook notification for a terminal review state.

    Failures are logged and silently ignored so the worker queue is not blocked.

    Args:
        review_id: The review identifier.
        brief_id: The brief identifier.
        status: Terminal review status.
        score: Optional review score.
        webhook_url: Destination URL (review-specific or system default).
        error: Optional error message for failed reviews.
    """
    url = webhook_url or settings.arbiter_webhook_url
    if not url:
        return

    event = "review.completed" if status != ArbiterReviewStatus.FAILED else "review.failed"
    payload: dict = {
        "event": event,
        "review_id": str(review_id),
        "brief_id": str(brief_id),
        "status": status.value,
        "score": score,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if error:
        payload["error"] = error

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Webhook delivery failed for review %s to %s: %s",
            review_id,
            url,
            exc,
        )
