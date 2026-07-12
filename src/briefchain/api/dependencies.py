"""FastAPI dependency injection helpers."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from briefchain.api.exceptions import APIError
from briefchain.api.security import decode_access_token
from briefchain.api.services import invites as invite_service
from briefchain.database import SessionLocal
from briefchain.models import BriefInvite, User

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db_session() -> Generator[Session]:
    """Yield a SQLAlchemy database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_db_session)]


def get_current_user_id(token: Annotated[str, Depends(_oauth2_scheme)]) -> UUID:
    """Decode the bearer token and return the user ID."""
    try:
        return decode_access_token(token)
    except ValueError as exc:
        raise APIError(
            code="UNAUTHORIZED",
            message=str(exc),
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc


CurrentUserIdDep = Annotated[UUID, Depends(get_current_user_id)]


def get_current_user(
    session: SessionDep,
    user_id: CurrentUserIdDep,
) -> User:
    """Load the currently authenticated user from the database."""
    user = session.get(User, user_id)
    if user is None:
        raise APIError(
            code="USER_NOT_FOUND",
            message="Authenticated user not found",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_invite_from_token(
    session: SessionDep,
    token: str,
) -> BriefInvite:
    """Validate an invite token and return the loaded BriefInvite record."""
    return invite_service.get_invite_by_token(session, token)


InviteDep = Annotated[BriefInvite, Depends(get_invite_from_token)]
