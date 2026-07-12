"""Tests for the database-backed task queue."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from briefchain.arbiter.queue.database import DatabaseTaskQueue
from briefchain.models.task_queue import TaskQueue as TaskQueueModel


def test_enqueue_creates_task(db_session: Session) -> None:
    """Enqueue inserts a row into the task_queue table."""
    queue = DatabaseTaskQueue()
    ref_id = uuid4()

    with db_session.begin():
        task = queue.enqueue(db_session, "review", ref_id)

    assert task.type == "review"
    assert task.ref_id == ref_id
    row = db_session.get(TaskQueueModel, task.id)
    assert row is not None
    assert row.type == "review"
    assert row.ref_id == ref_id


def test_dequeue_returns_oldest_task(db_session: Session) -> None:
    """Dequeue returns tasks in FIFO order."""
    queue = DatabaseTaskQueue()
    ref_ids = [uuid4() for _ in range(3)]

    with db_session.begin():
        for ref_id in ref_ids:
            queue.enqueue(db_session, "review", ref_id)

    results = []
    for _ in range(3):
        with db_session.begin():
            task = queue.dequeue(db_session)
        assert task is not None
        results.append(task.ref_id)

    assert results == ref_ids


def test_dequeue_removes_task(db_session: Session) -> None:
    """Dequeue deletes the returned task from the queue."""
    queue = DatabaseTaskQueue()
    ref_id = uuid4()

    with db_session.begin():
        task = queue.enqueue(db_session, "review", ref_id)
    with db_session.begin():
        queue.dequeue(db_session)

    assert db_session.get(TaskQueueModel, task.id) is None


def test_dequeue_returns_none_when_empty(db_session: Session) -> None:
    """Dequeue returns None when no tasks are pending."""
    queue = DatabaseTaskQueue()

    with db_session.begin():
        task = queue.dequeue(db_session)

    assert task is None
