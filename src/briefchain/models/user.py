"""SQLAlchemy models for the User sub-system."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
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

    # Set when a registered user is upgraded/linked from a temporary user.
    from_temporary_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

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
