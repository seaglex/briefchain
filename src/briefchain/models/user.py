"""SQLAlchemy models for the User sub-system."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from briefchain.models.base import Base, TimestampMixin
from briefchain.models.enums import UserType

if TYPE_CHECKING:
    pass


class User(Base, TimestampMixin):
    """User entity supporting registered, OAuth, external, and temporary accounts."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user_type: Mapped[UserType] = mapped_column(
        String(20),
        nullable=False,
        default=UserType.REGISTERED,
    )

    # Only used by registered users.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Only used by external users.
    source_system: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    identities: Mapped[list[UserIdentity]] = relationship(
        "UserIdentity",
        lazy="raise",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserIdentity(Base, TimestampMixin):
    """OAuth identity binding for a user."""

    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_user_identity_provider"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped[User] = relationship(
        "User",
        lazy="raise",
        back_populates="identities",
    )


class EmailToken(Base, TimestampMixin):
    """Access token sent to a temporary user via email."""

    __tablename__ = "email_tokens"

    token: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brief_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
