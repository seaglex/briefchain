"""SQLAlchemy models for the Feedback sub-system."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from briefchain.models.base import Base, TimestampMixin
from briefchain.models.enums import ArbiterReviewStatus, FeedbackType

if TYPE_CHECKING:
    from briefchain.models.brief import Brief


class Feedback(Base, TimestampMixin):
    """Feedback sent by a downstream about a brief."""

    __tablename__ = "feedbacks"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    brief_id: Mapped[UUID] = mapped_column(
        ForeignKey("briefs.brief_id"),
        nullable=False,
        index=True,
    )
    brief_version: Mapped[int] = mapped_column(Integer, nullable=False)

    type: Mapped[FeedbackType] = mapped_column(String(20), nullable=False)
    is_auto_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    from_user: Mapped[UUID] = mapped_column(nullable=False, index=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    brief: Mapped[Brief] = relationship(
        "Brief",
        lazy="raise",
        back_populates="feedbacks",
    )
    arbiter_reviews: Mapped[list[FeedbackArbiterReview]] = relationship(
        "FeedbackArbiterReview",
        lazy="raise",
        back_populates="feedback",
        order_by="FeedbackArbiterReview.created_at.desc()",
    )


class FeedbackArbiterReview(Base, TimestampMixin):
    """Arbiter review record for a feedback before it is sent upstream."""

    __tablename__ = "feedback_arbiter_reviews"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    feedback_id: Mapped[UUID] = mapped_column(
        ForeignKey("feedbacks.id"),
        nullable=False,
        index=True,
    )

    arbiter_id: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[ArbiterReviewStatus] = mapped_column(
        String(20),
        nullable=False,
    )
    result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    feedback: Mapped[Feedback] = relationship(
        "Feedback",
        lazy="raise",
        back_populates="arbiter_reviews",
    )
