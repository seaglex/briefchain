"""SQLAlchemy models for the Brief sub-system."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from briefchain.models.base import Base, TimestampMixin
from briefchain.models.enums import (
    ArbiterReviewStatus,
    BriefDownstreamState,
    BriefPriority,
    BriefType,
    BriefUpstreamState,
    BriefVersionStatus,
)

if TYPE_CHECKING:
    from briefchain.models.feedback import Feedback
    from briefchain.models.invite import BriefInvite


class Brief(Base, TimestampMixin):
    """Core entity representing a unit of work handed from upstream to downstream.

    A brief may be a root idea, a spec, or a leaf task. Root briefs form a chain;
    all briefs in the same chain share the same ``root_id``.
    """

    __tablename__ = "briefs"

    brief_id: Mapped[UUID] = mapped_column(primary_key=True)
    root_id: Mapped[UUID] = mapped_column(
        ForeignKey("briefs.brief_id"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("briefs.brief_id"),
        nullable=True,
    )
    is_root: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    current_version: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    upstream_state: Mapped[BriefUpstreamState] = mapped_column(
        String(20),
        nullable=False,
        default=BriefUpstreamState.EDITING,
    )
    downstream_state: Mapped[BriefDownstreamState | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[BriefType] = mapped_column(
        String(20),
        nullable=False,
        default=BriefType.IDEA,
    )
    priority: Mapped[BriefPriority] = mapped_column(
        String(10),
        nullable=False,
        default=BriefPriority.P2,
    )
    expected_completion_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by: Mapped[UUID] = mapped_column(nullable=False, index=True)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_to: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    assigned_to_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    status_changed_by: Mapped[UUID] = mapped_column(nullable=False)
    status_changed_by_name: Mapped[str] = mapped_column(String(255), nullable=False)

    parent: Mapped[Brief | None] = relationship(
        "Brief",
        lazy="raise",
        remote_side="Brief.brief_id",
        foreign_keys=[parent_id],
        back_populates="children",
    )
    children: Mapped[list[Brief]] = relationship(
        "Brief",
        lazy="raise",
        foreign_keys=[parent_id],
        back_populates="parent",
    )
    versions: Mapped[list[BriefVersion]] = relationship(
        "BriefVersion",
        lazy="raise",
        back_populates="brief",
        order_by="BriefVersion.version.asc()",
    )
    transfers: Mapped[list[BriefTransferHistory]] = relationship(
        "BriefTransferHistory",
        lazy="raise",
        back_populates="brief",
        order_by="BriefTransferHistory.sent_at.desc()",
    )
    arbiter_reviews: Mapped[list[BriefArbiterReview]] = relationship(
        "BriefArbiterReview",
        lazy="raise",
        back_populates="brief",
        order_by="BriefArbiterReview.reviewed_at.desc()",
    )
    feedbacks: Mapped[list[Feedback]] = relationship(
        "Feedback",
        lazy="raise",
        back_populates="brief",
        order_by="Feedback.created_at.desc()",
    )
    invites: Mapped[list[BriefInvite]] = relationship(
        "BriefInvite",
        lazy="raise",
        back_populates="brief",
        order_by="BriefInvite.created_at.desc()",
    )


class BriefVersion(Base, TimestampMixin):
    """Immutable snapshot of a brief's content at a specific version."""

    __tablename__ = "brief_versions"

    brief_id: Mapped[UUID] = mapped_column(
        ForeignKey("briefs.brief_id"),
        primary_key=True,
    )
    version: Mapped[int] = mapped_column(Integer, primary_key=True)

    status: Mapped[BriefVersionStatus] = mapped_column(
        String(20),
        nullable=False,
        default=BriefVersionStatus.DRAFT,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[BriefType] = mapped_column(
        String(20),
        nullable=False,
        default=BriefType.IDEA,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[list[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    priority: Mapped[BriefPriority] = mapped_column(
        String(10),
        nullable=False,
        default=BriefPriority.P2,
    )
    estimated_man_days: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    expected_completion_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    arbiter_review_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("brief_arbiter_reviews.id"),
        nullable=True,
    )

    is_upstream_changed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    revision_reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="initial",
    )

    modified_by: Mapped[UUID] = mapped_column(nullable=False)
    modified_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    change_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    brief: Mapped[Brief] = relationship(
        "Brief",
        lazy="raise",
        back_populates="versions",
    )
    arbiter_review: Mapped[BriefArbiterReview | None] = relationship(
        "BriefArbiterReview",
        lazy="raise",
        foreign_keys=[arbiter_review_id],
    )


class BriefTransferHistory(Base, TimestampMixin):
    """Record of a brief being sent from upstream to downstream."""

    __tablename__ = "brief_transfer_history"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    brief_id: Mapped[UUID] = mapped_column(
        ForeignKey("briefs.brief_id"),
        nullable=False,
        index=True,
    )
    brief_version: Mapped[int] = mapped_column(Integer, nullable=False)

    arbiter_review_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("brief_arbiter_reviews.id"),
        nullable=True,
    )

    from_user: Mapped[UUID] = mapped_column(nullable=False, index=True)
    from_user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    to_user: Mapped[UUID] = mapped_column(nullable=False, index=True)
    to_user_name: Mapped[str] = mapped_column(String(255), nullable=False)

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    brief: Mapped[Brief] = relationship(
        "Brief",
        lazy="raise",
        back_populates="transfers",
    )
    arbiter_review: Mapped[BriefArbiterReview | None] = relationship(
        "BriefArbiterReview",
        lazy="raise",
        foreign_keys=[arbiter_review_id],
    )


class BriefChain(Base, TimestampMixin):
    """Chain-level metadata. The root brief itself is the chain representative."""

    __tablename__ = "brief_chains"

    chain_id: Mapped[UUID] = mapped_column(
        ForeignKey("briefs.brief_id"),
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    owner_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[BriefPriority] = mapped_column(
        String(10),
        nullable=False,
        default=BriefPriority.P2,
    )

    root_brief: Mapped[Brief] = relationship(
        "Brief",
        lazy="raise",
        foreign_keys=[chain_id],
        primaryjoin="BriefChain.chain_id == Brief.brief_id",
    )


class BriefArbiterReview(Base, TimestampMixin):
    """Arbiter review record for a brief before it is sent downstream."""

    __tablename__ = "brief_arbiter_reviews"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    brief_id: Mapped[UUID] = mapped_column(
        ForeignKey("briefs.brief_id"),
        nullable=False,
        index=True,
    )
    brief_version: Mapped[int] = mapped_column(Integer, nullable=False)

    arbiter_id: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[ArbiterReviewStatus] = mapped_column(
        String(20),
        nullable=False,
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    issues: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    suggestions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    brief: Mapped[Brief] = relationship(
        "Brief",
        lazy="raise",
        back_populates="arbiter_reviews",
    )
    transfers: Mapped[list[BriefTransferHistory]] = relationship(
        "BriefTransferHistory",
        lazy="raise",
        back_populates="arbiter_review",
    )
