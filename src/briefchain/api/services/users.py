"""Business logic service for user-related operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from briefchain.api.exceptions import APIError
from briefchain.api.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserAuthBase
from briefchain.api.schemas.users import UserListResponse, UserResponse, serialize_user
from briefchain.api.security import create_access_token, get_password_hash, verify_password
from briefchain.models import Brief, BriefInvite, User
from briefchain.models.enums import BriefUpstreamState, UserType

_ACTIVE_BRIEF_UPSTREAM_STATES = {
    BriefUpstreamState.EDITING,
    BriefUpstreamState.SENT,
    BriefUpstreamState.IN_PROCESS,
    BriefUpstreamState.SUSPENDED,
}


def _migrate_active_briefs(
    session: Session,
    temporary_user_id: UUID,
    registered_user_id: UUID,
) -> None:
    """Reassign all non-done/non-cancelled briefs from a temporary user to a registered user."""
    active_briefs = (
        session.execute(
            select(Brief).where(
                Brief.assigned_to == temporary_user_id,
                Brief.upstream_state.in_(_ACTIVE_BRIEF_UPSTREAM_STATES),
            )
        )
        .scalars()
        .all()
    )

    for brief in active_briefs:
        brief.assigned_to = registered_user_id
        session.add(brief)


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


def _get_invite_from_token(
    session: Session,
    invite_token: str | None,
) -> BriefInvite:
    """Validate an invite token and return the corresponding invite record.

    Returns:
        The validated BriefInvite record.

    Raises:
        APIError: If the token is missing, invalid, expired, or invalidated.
    """
    from briefchain.api.services import invites as invite_service

    if not invite_token:
        raise APIError(
            code="INVALID_INVITE_TOKEN",
            message="invite_token is required",
            status_code=400,
        )

    return invite_service.get_invite_by_token(session, invite_token)


def register_user(session: Session, request: RegisterRequest) -> AuthResponse:
    """Register a new user with email or phone and a password."""
    from briefchain.api.services import invites as invite_service

    email = request.email
    phone = request.phone

    if not email and not phone:
        raise APIError(
            code="CONTACT_REQUIRED",
            message="At least one contact method (email or phone) is required",
            status_code=422,
        )

    existing = _find_existing_user(session, email, phone)
    has_invite = request.invite_token is not None
    if existing is not None:
        if has_invite:
            invite = _get_invite_from_token(session, request.invite_token)
            temporary_user = session.get(User, invite.temporary_user_id)
            if temporary_user is None:
                raise APIError(
                    code="INVALID_INVITE_TOKEN",
                    message="Temporary user not found",
                    status_code=400,
                )
            if existing.id != temporary_user.id:
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
        else:
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

    upgraded_from_temporary = False
    if has_invite:
        invite = _get_invite_from_token(session, request.invite_token)
        temporary_user = session.get(User, invite.temporary_user_id)
        if temporary_user is None:
            raise APIError(
                code="INVALID_INVITE_TOKEN",
                message="Temporary user not found",
                status_code=400,
            )
        user = temporary_user
        user.user_type = UserType.REGISTERED
        user.password_hash = get_password_hash(request.password)
        user.name = request.name
        user.email = email
        user.phone = phone
        user.from_temporary_user_id = temporary_user.id
        upgraded_from_temporary = True
        _migrate_active_briefs(session, temporary_user.id, user.id)
        invite_service.invalidate_invites_for_temporary_user(
            session=session,
            temporary_user_id=temporary_user.id,
            final_user_id=user.id,
        )
    else:
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
        upgraded_from_temporary=upgraded_from_temporary,
    )


def login_user(session: Session, request: LoginRequest) -> AuthResponse:
    """Authenticate a user with email/phone and password."""
    from briefchain.api.services import invites as invite_service

    email = request.email
    phone = request.phone

    if not email and not phone:
        raise APIError(
            code="CONTACT_REQUIRED",
            message="At least one contact method (email or phone) is required",
            status_code=422,
        )

    user = _find_existing_user(session, email, phone)

    if user is None:
        raise APIError(
            code="INVALID_CREDENTIALS",
            message="Invalid email/phone or password",
            status_code=401,
        )

    if user.user_type == UserType.TEMPORARY:
        raise APIError(
            code="TEMPORARY_USER_CANNOT_LOGIN",
            message="Temporary users cannot log in with a password. Please use the invite link.",
            status_code=401,
        )

    if user.password_hash is None or not verify_password(request.password, user.password_hash):
        raise APIError(
            code="INVALID_CREDENTIALS",
            message="Invalid email/phone or password",
            status_code=401,
        )

    linked_temporary_user: UUID | None = None
    if request.invite_token is not None:
        invite = _get_invite_from_token(session, request.invite_token)
        temporary_user = session.get(User, invite.temporary_user_id)
        if temporary_user is None:
            raise APIError(
                code="INVALID_INVITE_TOKEN",
                message="Temporary user not found",
                status_code=400,
            )
        _migrate_active_briefs(session, temporary_user.id, user.id)
        user.from_temporary_user_id = temporary_user.id
        linked_temporary_user = temporary_user.id
        invite_service.invalidate_invites_for_temporary_user(
            session=session,
            temporary_user_id=temporary_user.id,
            final_user_id=user.id,
        )

    session.commit()
    session.refresh(user)

    token = create_access_token(user.id)
    return AuthResponse(
        user=UserAuthBase.model_validate(user),
        token=token,
        linked_temporary_user=linked_temporary_user,
    )


def get_current_user_profile(current_user: User) -> UserResponse:
    """Return the current authenticated user's profile."""
    return UserResponse.model_validate(serialize_user(current_user, viewer_user_id=current_user.id))


def list_users(
    session: Session,
    viewer_user_id: UUID,
    page: int,
    page_size: int,
) -> UserListResponse:
    """Return a paginated list of registered users with masked sensitive fields.

    Temporary users are excluded because they should not be discoverable in
    the public user list.
    """
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    total = (
        session.execute(
            select(func.count())
            .select_from(User)
            .where(User.user_type != UserType.TEMPORARY)
        ).scalar()
        or 0
    )

    users = (
        session.execute(
            select(User)
            .where(User.user_type != UserType.TEMPORARY)
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
    """Return a single user's profile with viewer-aware masking."""
    user = session.get(User, user_id)
    if user is None:
        raise APIError(
            code="USER_NOT_FOUND",
            message="User not found",
            status_code=404,
        )

    return UserResponse.model_validate(serialize_user(user, viewer_user_id=viewer_user_id))
