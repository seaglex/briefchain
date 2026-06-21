"""Unit tests for User data models."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from briefchain.models import (
    EmailToken,
    User,
    UserIdentity,
    UserType,
)


def test_create_all_user_types(db_session) -> None:
    """Create one user of each supported user type."""
    registered = User(
        id=uuid4(),
        email="registered@example.com",
        name="Registered User",
        user_type=UserType.REGISTERED,
        password_hash="fake_hash",
    )
    oauth = User(
        id=uuid4(),
        email="oauth@example.com",
        name="OAuth User",
        user_type=UserType.OAUTH,
    )
    external = User(
        id=uuid4(),
        name="External User",
        user_type=UserType.EXTERNAL,
        source_system="external.example.com",
        external_ref=str(uuid4()),
    )
    temporary = User(
        id=uuid4(),
        email="temp@example.com",
        name="Temporary User",
        user_type=UserType.TEMPORARY,
    )

    db_session.add_all([registered, oauth, external, temporary])
    db_session.commit()

    users = db_session.execute(select(User).order_by(User.name)).scalars().all()
    assert len(users) == 4
    assert {u.user_type for u in users} == {
        UserType.REGISTERED,
        UserType.OAUTH,
        UserType.EXTERNAL,
        UserType.TEMPORARY,
    }


def test_user_type_enum_rejects_invalid_value() -> None:
    """UserType enum rejects unsupported values."""
    with pytest.raises(ValueError):  # noqa: PT011
        UserType("invalid")


def test_bind_multiple_identities_to_user(db_session) -> None:
    """A registered user can bind multiple OAuth identities."""
    user = User(
        id=uuid4(),
        email="multi@example.com",
        name="Multi Identity User",
        user_type=UserType.REGISTERED,
    )
    github = UserIdentity(
        id=uuid4(),
        user_id=user.id,
        provider="github",
        provider_user_id="github_123",
    )
    google = UserIdentity(
        id=uuid4(),
        user_id=user.id,
        provider="google",
        provider_user_id="google_456",
    )

    db_session.add_all([user, github, google])
    db_session.commit()

    loaded = db_session.execute(
        select(User).where(User.id == user.id).options(selectinload(User.identities))
    ).scalar_one()
    assert len(loaded.identities) == 2
    assert {i.provider for i in loaded.identities} == {"github", "google"}


def test_duplicate_provider_identity_rejected(db_session) -> None:
    """The same provider and provider_user_id cannot be bound twice."""
    user = User(
        id=uuid4(),
        email="dup@example.com",
        name="Duplicate Identity User",
        user_type=UserType.REGISTERED,
    )
    first = UserIdentity(
        id=uuid4(),
        user_id=user.id,
        provider="github",
        provider_user_id="github_123",
    )
    duplicate = UserIdentity(
        id=uuid4(),
        user_id=user.id,
        provider="github",
        provider_user_id="github_123",
    )

    db_session.add_all([user, first])
    db_session.commit()

    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_create_and_use_email_token(db_session) -> None:
    """Create an email token and mark it as used."""
    brief_id = uuid4()
    token = EmailToken(
        token=str(uuid4()),
        email="external@example.com",
        brief_id=brief_id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    db_session.add(token)
    db_session.commit()

    loaded = db_session.execute(
        select(EmailToken).where(EmailToken.token == token.token)
    ).scalar_one()
    assert loaded.used_at is None

    loaded.used_at = datetime.now(UTC)
    db_session.commit()

    reloaded = db_session.execute(
        select(EmailToken).where(EmailToken.token == token.token)
    ).scalar_one()
    assert reloaded.used_at is not None
