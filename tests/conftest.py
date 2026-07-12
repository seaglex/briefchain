"""Pytest fixtures for BriefChain model and API tests."""

from collections.abc import Generator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from briefchain.api.config import settings
from briefchain.api.dependencies import get_db_session
from briefchain.api.main import app
from briefchain.api.security import create_access_token, get_password_hash
from briefchain.models import Brief, BriefChain, BriefVersion, User
from briefchain.models.base import Base
from briefchain.models.enums import (
    BriefPriority,
    BriefUpstreamState,
    BriefVersionStatus,
    UserType,
)


@pytest.fixture
def db_session() -> Generator[Session]:
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)  # noqa: N806
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    """Create a FastAPI test client with an overridden database session."""
    settings.arbiter_worker_spawn = False

    def _get_test_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db_session] = _get_test_db
    try:
        yield TestClient(app)
    finally:
        del app.dependency_overrides[get_db_session]


@pytest.fixture
def jwt_secret(monkeypatch: pytest.MonkeyPatch) -> str:
    """Set a fixed JWT secret for deterministic tests."""
    secret = "test-jwt-secret-key-do-not-use-in-production"
    monkeypatch.setattr(settings, "jwt_secret_key", secret)
    return secret


@pytest.fixture
def auth_headers(jwt_secret: str, db_session: Session) -> dict[str, str]:
    """Return authorization headers for a default registered user.

    Creates the user in the provided database session.
    """
    user = User(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        email="test@example.com",
        name="Test User",
        user_type=UserType.REGISTERED,
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def creator(db_session: Session) -> User:
    """Create a registered user to use as brief creator."""
    user = User(
        id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        email="creator@example.com",
        name="Creator",
        user_type=UserType.REGISTERED,
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def downstream(db_session: Session) -> User:
    """Create a registered user to use as downstream."""
    user = User(
        id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        email="downstream@example.com",
        name="Downstream",
        user_type=UserType.REGISTERED,
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def other_user(db_session: Session) -> User:
    """Create another registered user."""
    user = User(
        id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        email="other@example.com",
        name="Other",
        user_type=UserType.REGISTERED,
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_headers_creator(jwt_secret: str, db_session: Session, creator: User) -> dict[str, str]:
    """Return authorization headers for the creator user."""
    token = create_access_token(creator.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_downstream(
    jwt_secret: str,
    db_session: Session,
    downstream: User,
) -> dict[str, str]:
    """Return authorization headers for the downstream user."""
    token = create_access_token(downstream.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_other_user(
    jwt_secret: str,
    db_session: Session,
    other_user: User,
) -> dict[str, str]:
    """Return authorization headers for the other user."""
    token = create_access_token(other_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def draft_brief(db_session: Session, creator: User) -> Brief:
    """Create a draft brief owned by creator."""
    brief = Brief(
        brief_id=UUID("11111111-1111-1111-1111-111111111111"),
        root_id=UUID("11111111-1111-1111-1111-111111111111"),
        parent_id=None,
        is_root=True,
        upstream_state=BriefUpstreamState.EDITING,
        downstream_state=None,
        current_version=None,
        title="Draft Brief",
        priority=BriefPriority.P2,
        expected_completion_at=None,
        created_by=creator.id,
        created_by_name=creator.name,
        assigned_to=None,
        assigned_to_name=None,
        status_changed_by=creator.id,
        status_changed_by_name=creator.name,
        status_changed_at=datetime.now(UTC),
    )
    version = BriefVersion(
        brief_id=brief.brief_id,
        version=1,
        status=BriefVersionStatus.DRAFT,
        title="Draft Brief",
        content="Content",
        attachments=[],
        priority=BriefPriority.P2,
        estimated_man_days=3.0,
        expected_completion_at=None,
        arbiter_review_id=None,
        is_upstream_changed=False,
        revision_reason="initial",
        modified_by=creator.id,
        modified_by_name=creator.name,
        change_summary="Initial version",
    )
    chain = BriefChain(
        chain_id=brief.brief_id,
        title="Draft Brief",
        owner_id=creator.id,
        owner_name=creator.name,
        priority=BriefPriority.P2,
    )
    db_session.add_all([brief, version, chain])
    db_session.commit()
    return brief
