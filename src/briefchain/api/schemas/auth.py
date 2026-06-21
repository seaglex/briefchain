"""Pydantic schemas for authentication endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from briefchain.models.enums import UserType


class UserAuthBase(BaseModel):
    """Base authentication response user payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str | None
    phone: str | None
    avatar_url: str | None
    user_type: UserType


class AuthResponse(BaseModel):
    """Response returned on successful registration or login."""

    user: UserAuthBase
    token: str


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr | None = Field(default=None, examples=["user@example.com"])
    phone: str | None = Field(default=None, pattern=r"^\+?1?\d{9,15}$", examples=["+8613800000000"])
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("email", "phone", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        """Strip whitespace from contact fields."""
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        """Normalize phone to None if empty."""
        if value is not None and not value.strip():
            return None
        return value


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr | None = Field(default=None, examples=["user@example.com"])
    phone: str | None = Field(default=None, examples=["+8613800000000"])
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email", "phone", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        """Strip whitespace from contact fields."""
        if isinstance(value, str):
            return value.strip() or None
        return value
