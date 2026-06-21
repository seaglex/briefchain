"""Authentication routes for the BriefChain API."""

from fastapi import APIRouter, status

from briefchain.api.dependencies import CurrentUserDep, SessionDep
from briefchain.api.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from briefchain.api.schemas.users import UserResponse
from briefchain.api.services.users import (
    get_current_user_profile,
    login_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(session: SessionDep, request: RegisterRequest) -> AuthResponse:
    """Register a new user with email or phone and a password."""
    return register_user(session, request)


@router.post("/login", response_model=AuthResponse)
def login(session: SessionDep, request: LoginRequest) -> AuthResponse:
    """Authenticate a user with email/phone and password."""
    return login_user(session, request)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUserDep) -> UserResponse:
    """Return the current authenticated user's profile."""
    return get_current_user_profile(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: CurrentUserDep) -> None:  # noqa: ARG001
    """Logout endpoint; client is responsible for clearing the token."""
    return None
