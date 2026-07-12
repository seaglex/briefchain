"""SQLAlchemy model for the generic asynchronous task queue."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from briefchain.models.base import Base, TimestampMixin


class TaskQueue(Base, TimestampMixin):
    """Generic FIFO queue for asynchronous tasks.

    The queue only stores task identity and creation time. Lifecycle state,
    retries, and results are managed by the business layer (e.g.
    ``brief_arbiter_reviews``).
    """

    __tablename__ = "task_queue"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    ref_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    __table_args__ = (
        Index("idx_queue_fetch", "created_at"),
    )
