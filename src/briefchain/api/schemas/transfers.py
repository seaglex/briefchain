"""Pydantic schemas for brief transfer endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransferListItem(BaseModel):
    """Transfer history list item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brief_version: int
    from_user_id: UUID
    from_user_name: str
    to_user_id: UUID
    to_user_name: str
    sent_at: str
    accepted_at: str | None
    rejected_at: str | None
    rejection_reason: str | None
