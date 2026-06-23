"""SQLAlchemy models for Brief invitations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from briefchain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from briefchain.models.brief import Brief
    from briefchain.models.user import User


class BriefInvite(Base, TimestampMixin):
    """Invitation link for an external (temporary) user to access a brief."""

    __tablename__ = "brief_invites"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    brief_id: Mapped[UUID] = mapped_column(
        ForeignKey("briefs.brief_id"),
        nullable=False,
        index=True,
    )
    nonce: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        unique=True,
        index=True,
    )
    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    temporary_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    from_user: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    final_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    accept_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    complete_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    invalidated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    brief: Mapped[Brief] = relationship(
        "Brief",
        lazy="raise",
        back_populates="invites",
    )
    temporary_user: Mapped[User] = relationship(
        "User",
        lazy="raise",
        foreign_keys=[temporary_user_id],
    )
    sender: Mapped[User] = relationship(
        "User",
        lazy="raise",
        foreign_keys=[from_user],
    )
