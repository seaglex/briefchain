"""Tests for the users API endpoints."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from briefchain.models import User
from briefchain.models.enums import UserType


@pytest.fixture
def other_user(db_session: Session) -> User:
    """Create a second user for list/detail tests."""
    user = User(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        email="other@example.com",
        phone="+8613922222222",
        name="Other User",
        user_type=UserType.REGISTERED,
        password_hash="fake_hash",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def temporary_user(db_session: Session) -> User:
    """Create a temporary user that should not appear in the public list."""
    user = User(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        email=None,
        phone=None,
        name="Temporary User",
        user_type=UserType.TEMPORARY,
        password_hash=None,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_list_users_returns_masked_fields(
    client: TestClient,
    auth_headers: dict[str, str],
    other_user: User,
) -> None:
    """The user list masks sensitive fields for other users."""
    response = client.get("/api/v1/users", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2

    other = next(item for item in data["items"] if item["id"] == str(other_user.id))
    assert other["email"] == "***@example.com"
    assert other["phone"] == "+86****2222"


def test_list_users_excludes_temporary_users(
    client: TestClient,
    auth_headers: dict[str, str],
    other_user: User,
    temporary_user: User,
) -> None:
    """The user list must not expose temporary users."""
    response = client.get("/api/v1/users", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    returned_ids = {item["id"] for item in data["items"]}
    assert str(other_user.id) in returned_ids
    assert str(temporary_user.id) not in returned_ids


def test_list_users_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Pagination query parameters are respected."""
    response = client.get("/api/v1/users?page=1&page_size=5", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5


def test_get_own_profile_shows_unmasked_fields(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Viewing your own profile returns unmasked email and phone."""
    user_id = "12345678-1234-5678-1234-567812345678"
    response = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "test@example.com"


def test_get_other_user_profile_masks_fields(
    client: TestClient,
    auth_headers: dict[str, str],
    other_user: User,
) -> None:
    """Viewing another user's profile masks email and phone."""
    response = client.get(f"/api/v1/users/{other_user.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "***@example.com"
    assert data["phone"] == "+86****2222"


def test_get_user_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Requesting a non-existent user returns 404."""
    response = client.get(
        "/api/v1/users/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )

    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "USER_NOT_FOUND"
