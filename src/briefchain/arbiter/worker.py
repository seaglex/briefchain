"""Arbiter background worker implementation."""

from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from briefchain.api.config import settings
from briefchain.arbiter.handlers.review import (
    ReviewHandler,
    TransientReviewError,
    notify_terminal_state,
)
from briefchain.arbiter.queue.base import QueueTask, TaskQueue
from briefchain.arbiter.queue.factory import create_queue
from briefchain.database import SessionLocal
from briefchain.models import BriefArbiterReview
from briefchain.models.enums import ArbiterReviewStatus

logger = logging.getLogger(__name__)


_TERMINAL_STATUSES = {
    ArbiterReviewStatus.PASSED,
    ArbiterReviewStatus.REJECTED,
    ArbiterReviewStatus.FAILED,
    ArbiterReviewStatus.FORCE_SKIPPED,
}


@contextmanager
def _managed_transaction(session: Session) -> Generator[Session]:
    """Begin a transaction only when the session is not already in one."""
    if session.in_transaction():
        yield session
    else:
        with session.begin():
            yield session


class ArbiterWorker:
    """Background worker that consumes tasks from the queue and executes them."""

    def __init__(
        self,
        queue: TaskQueue | None = None,
        poll_interval: float | None = None,
        max_retries: int | None = None,
        health_check_interval: float | None = None,
        processing_timeout: float | None = None,
        session_factory=None,
    ) -> None:
        """Initialize the worker with configurable intervals.

        Args:
            queue: Task queue instance. Defaults to ``create_queue()``.
            poll_interval: Seconds to sleep when the queue is empty.
            max_retries: Maximum attempts before marking a review failed.
            health_check_interval: Seconds between health recovery scans.
            processing_timeout: Seconds after which a processing review is stuck.
            session_factory: Optional callable returning a SQLAlchemy session.
        """
        self.queue = queue if queue is not None else create_queue()
        self.poll_interval = (
            poll_interval if poll_interval is not None else settings.worker_poll_interval
        )
        self.max_retries = max_retries if max_retries is not None else settings.worker_max_retries
        self.health_check_interval = (
            health_check_interval
            if health_check_interval is not None
            else settings.worker_health_check_interval
        )
        self.processing_timeout = (
            processing_timeout
            if processing_timeout is not None
            else settings.worker_processing_timeout
        )
        self._session_factory = session_factory if session_factory is not None else SessionLocal

        self._running = False
        self._last_health_check: datetime | None = None
        self._handlers: dict[str, Any] = {
            "review": ReviewHandler(),
        }

    async def run(self) -> None:
        """Run the worker loop until a shutdown signal is received."""
        self._running = True
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_signal)

        logger.info("Arbiter worker started")

        try:
            await self._health_recovery()
            self._last_health_check = datetime.now(UTC)

            while self._running:
                await self._maybe_health_recovery()
                task = await self._dequeue()
                if task is None:
                    await asyncio.sleep(self.poll_interval)
                    continue
                await self._process_task(task)
        finally:
            logger.info("Arbiter worker shutting down")

    def _handle_signal(self) -> None:
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received")
        self._running = False

    async def _maybe_health_recovery(self) -> None:
        """Run health recovery if the configured interval has passed."""
        now = datetime.now(UTC)
        if (
            self._last_health_check is None
            or (now - self._last_health_check).total_seconds() >= self.health_check_interval
        ):
            await self._health_recovery()
            self._last_health_check = now

    async def _health_recovery(self) -> None:
        """Re-enqueue reviews stuck in processing beyond the timeout."""
        cutoff = datetime.now(UTC) - timedelta(seconds=self.processing_timeout)
        with self._session_factory() as session, _managed_transaction(session):
            stuck_reviews = session.execute(
                select(BriefArbiterReview).where(
                    BriefArbiterReview.status == ArbiterReviewStatus.PROCESSING,
                    BriefArbiterReview.last_attempt_at < cutoff,
                )
            ).scalars().all()

            for review in stuck_reviews:
                logger.info("Recovering stuck review %s", review.id)
                self.queue.enqueue(session, "review", review.id)

    async def _dequeue(self) -> QueueTask | None:
        """Atomically dequeue the next task."""
        with self._session_factory() as session, _managed_transaction(session):
            return self.queue.dequeue(session)

    async def _process_task(self, task: QueueTask) -> None:
        """Process a single task with retry logic."""
        logger.info("Processing task %s of type %s", task.id, task.type)

        handler = self._handlers.get(task.type)
        if handler is None:
            logger.warning("Unknown task type: %s", task.type)
            return

        with self._session_factory() as session, _managed_transaction(session):
            review = session.get(BriefArbiterReview, task.ref_id)
            if review is None:
                logger.warning("Review %s not found", task.ref_id)
                return

            if review.status in _TERMINAL_STATUSES:
                logger.info("Review %s already terminal (%s)", review.id, review.status)
                return

            if review.attempt_count >= self.max_retries:
                logger.warning("Review %s exceeded max retries", review.id)
                review.status = ArbiterReviewStatus.FAILED
                review.error = "max retries exceeded"
                review.reviewed_at = datetime.now(UTC)
                session.flush()
                await notify_terminal_state(review)
                return

            review.attempt_count += 1
            review.last_attempt_at = datetime.now(UTC)
            session.flush()

            task_ref_id = review.id

        try:
            with self._session_factory() as session, _managed_transaction(session):
                review = session.get(BriefArbiterReview, task_ref_id)
                assert review is not None
                await handler.execute(session, review)
                session.flush()
                await notify_terminal_state(review)
        except TransientReviewError as exc:
            logger.warning("Transient error for review %s: %s", task_ref_id, exc)
            with self._session_factory() as session, _managed_transaction(session):
                review = session.get(BriefArbiterReview, task_ref_id)
                assert review is not None
                review.error = str(exc)
                session.flush()
                self.queue.enqueue(session, task.type, review.id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error processing review %s", task_ref_id)
            with self._session_factory() as session, _managed_transaction(session):
                review = session.get(BriefArbiterReview, task_ref_id)
                assert review is not None
                review.error = str(exc)
                session.flush()
                self.queue.enqueue(session, task.type, review.id)


def main() -> None:
    """Synchronous entry point for the worker subprocess."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    worker = ArbiterWorker()
    asyncio.run(worker.run())
