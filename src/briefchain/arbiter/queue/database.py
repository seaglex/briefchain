"""Database-backed implementation of the task queue."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from briefchain.arbiter.queue.base import QueueTask, TaskQueue
from briefchain.models.task_queue import TaskQueue as TaskQueueModel


class DatabaseTaskQueue(TaskQueue):
    """Task queue implementation using the existing SQLAlchemy database."""

    def enqueue(self, session: Session, type: str, ref_id: UUID) -> QueueTask:
        """Insert a task into the queue."""
        task = TaskQueueModel(type=type, ref_id=ref_id)
        session.add(task)
        session.flush()
        return QueueTask(id=task.id, type=task.type, ref_id=task.ref_id)

    def dequeue(self, session: Session) -> QueueTask | None:
        """Remove and return the oldest pending task."""
        subquery = (
            select(TaskQueueModel.id)
            .order_by(TaskQueueModel.created_at.asc())
            .limit(1)
            .scalar_subquery()
        )
        stmt = (
            delete(TaskQueueModel)
            .where(TaskQueueModel.id == subquery)
            .returning(TaskQueueModel)
        )
        result = session.execute(stmt)
        row = result.mappings().one_or_none()
        if row is None:
            return None
        task = row[TaskQueueModel]
        return QueueTask(id=task.id, type=task.type, ref_id=task.ref_id)
