"""Pydantic schemas for user endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from briefchain.models.enums import UserType


def _mask_email(email: str | None) -> str | None:
    """Mask an email address for non-self viewers."""
    if email is None:
        return None
    return "***@example.com"


def _mask_phone(phone: str | None) -> str | None:
    """Mask a phone number for non-self viewers."""
    if phone is None:
        return None
    if len(phone) <= 7:
        return "****"
    return f"{phone[:3]}****{phone[-4:]}"


def serialize_user(user: object, viewer_user_id: UUID | None = None) -> dict:
    """Serialize a User model with viewer-aware masking.

    Args:
        user: SQLAlchemy User instance.
        viewer_user_id: ID of the user requesting the data; if equal to user.id,
            sensitive fields are returned unmasked.

    Returns:
        A dictionary suitable for UserResponse.model_validate.
    """
    is_self = viewer_user_id is not None and viewer_user_id == user.id
    email = user.email if is_self else _mask_email(user.email)
    phone = user.phone if is_self else _mask_phone(user.phone)

    return {
        "id": user.id,
        "name": user.name,
        "email": email,
        "phone": phone,
        "avatar_url": user.avatar_url,
        "user_type": user.user_type,
    }


class UserResponse(BaseModel):
    """Public user profile response with masked sensitive fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str | None
    phone: str | None
    avatar_url: str | None
    user_type: UserType


class UserListResponse(BaseModel):
    """Paginated list of users."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
