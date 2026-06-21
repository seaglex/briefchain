"""Business logic service for user-related operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from briefchain.api.exceptions import APIError
from briefchain.api.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserAuthBase
from briefchain.api.schemas.users import UserListResponse, UserResponse, serialize_user
from briefchain.api.security import create_access_token, get_password_hash, verify_password
from briefchain.models import User
from briefchain.models.enums import UserType


def _build_contact_filter(email: str | None, phone: str | None) -> object:
    """Build an OR filter matching email or phone when provided."""
    conditions = []
    if email is not None:
        conditions.append(User.email == email)
    if phone is not None:
        conditions.append(User.phone == phone)
    return or_(*conditions)


def _find_existing_user(
    session: Session,
    email: str | None,
    phone: str | None,
) -> User | None:
    """Return the first user matching the given email or phone."""
    filter_clause = _build_contact_filter(email, phone)
    return session.execute(select(User).where(filter_clause)).scalars().first()


def register_user(session: Session, request: RegisterRequest) -> AuthResponse:
    """Register a new user with email or phone and a password.

    Args:
        session: SQLAlchemy database session.
        request: Registration request containing email/phone, name, and password.

    Returns:
        Authentication response with the new user and a JWT token.

    Raises:
        APIError: If no contact method is provided or the contact is already registered.
    """
    email = request.email
    phone = request.phone

    if not email and not phone:
        raise APIError(
            code="CONTACT_REQUIRED",
            message="At least one contact method (email or phone) is required",
            status_code=422,
        )

    existing = _find_existing_user(session, email, phone)
    if existing is not None:
        if email and existing.email == email:
            raise APIError(
                code="EMAIL_ALREADY_REGISTERED",
                message="The email is already registered",
                status_code=409,
            )
        if phone and existing.phone == phone:
            raise APIError(
                code="PHONE_ALREADY_REGISTERED",
                message="The phone is already registered",
                status_code=409,
            )

    user = User(
        id=uuid4(),
        email=email,
        phone=phone,
        name=request.name,
        user_type=UserType.REGISTERED,
        password_hash=get_password_hash(request.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token(user.id)
    return AuthResponse(
        user=UserAuthBase.model_validate(user),
        token=token,
    )


def login_user(session: Session, request: LoginRequest) -> AuthResponse:
    """Authenticate a user with email/phone and password.

    Args:
        session: SQLAlchemy database session.
        request: Login request containing email/phone and password.

    Returns:
        Authentication response with the user and a JWT token.

    Raises:
        APIError: If no contact method is provided or credentials are invalid.
    """
    email = request.email
    phone = request.phone

    if not email and not phone:
        raise APIError(
            code="CONTACT_REQUIRED",
            message="At least one contact method (email or phone) is required",
            status_code=422,
        )

    user = _find_existing_user(session, email, phone)

    if (
        user is None
        or user.password_hash is None
        or not verify_password(request.password, user.password_hash)
    ):
        raise APIError(
            code="INVALID_CREDENTIALS",
            message="Invalid email/phone or password",
            status_code=401,
        )

    token = create_access_token(user.id)
    return AuthResponse(
        user=UserAuthBase.model_validate(user),
        token=token,
    )


def get_current_user_profile(current_user: User) -> UserResponse:
    """Return the current authenticated user's profile.

    Args:
        current_user: The authenticated user model.

    Returns:
        User response with unmasked sensitive fields.
    """
    return UserResponse.model_validate(serialize_user(current_user, viewer_user_id=current_user.id))


def list_users(
    session: Session,
    viewer_user_id: UUID,
    page: int,
    page_size: int,
) -> UserListResponse:
    """Return a paginated list of users with masked sensitive fields.

    Args:
        session: SQLAlchemy database session.
        viewer_user_id: ID of the user requesting the list; used for masking.
        page: 1-based page number.
        page_size: Number of items per page (will be clamped to [1, 100]).

    Returns:
        Paginated list of user responses.
    """
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    total = session.execute(select(func.count()).select_from(User)).scalar() or 0

    users = (
        session.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = [
        UserResponse.model_validate(serialize_user(user, viewer_user_id=viewer_user_id))
        for user in users
    ]

    return UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def get_user_by_id(
    session: Session,
    user_id: UUID,
    viewer_user_id: UUID,
) -> UserResponse:
    """Return a single user's profile with viewer-aware masking.

    Args:
        session: SQLAlchemy database session.
        user_id: ID of the user to retrieve.
        viewer_user_id: ID of the user requesting the profile; used for masking.

    Returns:
        User response with sensitive fields masked unless the viewer is the owner.

    Raises:
        APIError: If the requested user does not exist.
    """
    user = session.get(User, user_id)
    if user is None:
        raise APIError(
            code="USER_NOT_FOUND",
            message="User not found",
            status_code=404,
        )

    return UserResponse.model_validate(serialize_user(user, viewer_user_id=viewer_user_id))
