"""FastAPI dependency injection helpers."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from briefchain.api.config import settings
from briefchain.api.exceptions import APIError
from briefchain.api.security import decode_access_token
from briefchain.models import User

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    echo=False,
)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_db_session() -> Generator[Session]:
    """Yield a SQLAlchemy database session."""
    session = _SessionLocal()
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
