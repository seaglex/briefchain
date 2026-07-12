"""Abstract task queue interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class QueueTask:
    """A task returned from the queue."""

    id: UUID
    type: str
    ref_id: UUID


class TaskQueue(ABC):
    """Backend-agnostic FIFO task queue.

    The queue only stores and delivers tasks. Lifecycle state, retries, and
    results are the responsibility of the business layer.
    """

    @abstractmethod
    def enqueue(self, session, type: str, ref_id: UUID) -> QueueTask:
        """Insert a task into the queue and return it.

        Args:
            session: A SQLAlchemy session within an active transaction.
            type: Task type identifier (e.g. ``"review"``).
            ref_id: Reference ID for the business entity to process.

        Returns:
            The queued task.
        """

    @abstractmethod
    def dequeue(self, session) -> QueueTask | None:
        """Remove and return the oldest pending task, or ``None`` if empty.

        Args:
            session: A SQLAlchemy session within an active transaction.

        Returns:
            The oldest queued task, or ``None`` when the queue is empty.
        """
