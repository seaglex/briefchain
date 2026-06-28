"""User routes for the BriefChain API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from briefchain.api.dependencies import CurrentUserDep, SessionDep, get_current_user_id
from briefchain.api.schemas.users import UserListResponse, UserResponse
from briefchain.api.services.users import get_user_by_id, list_users

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user_id)],
)


@router.get("", response_model=UserListResponse)
def list_users_endpoint(
    session: SessionDep,
    current_user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> UserListResponse:
    """Return a paginated list of users with masked sensitive fields."""
    return list_users(
        session,
        viewer_user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    session: SessionDep,
    current_user: CurrentUserDep,
    user_id: UUID,
) -> UserResponse:
    """Return a single user's profile with viewer-aware masking."""
    return get_user_by_id(session, user_id=user_id, viewer_user_id=current_user.id)
