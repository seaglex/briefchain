"""Tests for the authentication API endpoints."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from briefchain.models import User
from briefchain.models.enums import UserType


@pytest.fixture
def existing_user(db_session: Session) -> User:
    """Create a registered user for login tests."""
    from briefchain.api.security import get_password_hash

    user = User(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        email="existing@example.com",
        name="Existing User",
        user_type=UserType.REGISTERED,
        password_hash=get_password_hash("securepassword"),
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_register_with_email_success(client: TestClient, jwt_secret: str) -> None:
    """A new user can register with email and password."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "name": "New User",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["name"] == "New User"
    assert data["user"]["user_type"] == "registered"
    assert "token" in data
    assert isinstance(data["token"], str)


def test_register_with_phone_success(client: TestClient, jwt_secret: str) -> None:
    """A new user can register with phone and password."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone": "+8613800000000",
            "name": "Phone User",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["phone"] == "+8613800000000"
    assert data["user"]["name"] == "Phone User"
    assert "token" in data


def test_register_requires_email_or_phone(client: TestClient, jwt_secret: str) -> None:
    """Registration fails when neither email nor phone is provided."""
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "No Contact", "password": "password123"},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "CONTACT_REQUIRED"


def test_register_rejects_duplicate_email(
    client: TestClient,
    jwt_secret: str,
    existing_user: User,
) -> None:
    """Registration fails for an already-registered email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": existing_user.email,
            "name": "Duplicate",
            "password": "password123",
        },
    )

    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_login_with_email_success(client: TestClient, existing_user: User) -> None:
    """A registered user can log in with email and password."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": existing_user.email,
            "password": "securepassword",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(existing_user.id)
    assert data["user"]["email"] == existing_user.email
    assert "token" in data


def test_login_with_phone_success(client: TestClient, existing_user: User) -> None:
    """A registered user can log in with phone and password."""
    existing_user.phone = "+8613811111111"
    # The client fixture shares the same session via dependency override.
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone": "+8613811111111",
            "password": "securepassword",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(existing_user.id)


def test_login_rejects_invalid_credentials(client: TestClient, existing_user: User) -> None:
    """Login fails for an unknown email or wrong password."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": existing_user.email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_get_current_user_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    """A valid token returns the current user's profile."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


def test_get_current_user_rejects_unauthenticated(client: TestClient) -> None:
    """Requests without a valid token are rejected."""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_logout_returns_no_content(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Logout returns 204 No Content."""
    response = client.post("/api/v1/auth/logout", headers=auth_headers)

    assert response.status_code == 204
    assert response.content == b""
