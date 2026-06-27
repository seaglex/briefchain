"""Business logic service for Brief invitations."""

from __future__ import annotations

import binascii
import hmac
import secrets
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from briefchain.api.config import settings
from briefchain.api.exceptions import APIError
from briefchain.models import BriefInvite


def _epoch_seconds(value: datetime) -> int:
    """Convert a datetime to Unix epoch seconds."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())


def _format_time(value: datetime) -> str:
    """Return ISO formatted datetime string."""
    return value.isoformat()


def _generate_nonce() -> str:
    """Generate a URL-safe random nonce."""
    return secrets.token_urlsafe(16)


def _sign_payload(payload: str) -> str:
    """Return hex HMAC-SHA256 signature for the payload."""
    signature = hmac.new(
        settings.jwt_secret_key.encode(),
        payload.encode(),
        sha256,
    ).hexdigest()
    return signature


def generate_invite_token(brief_id: UUID, nonce: str, accept_deadline: datetime) -> str:
    """Generate an HMAC-signed invite token.

    Token format: brief_id_hex:nonce:accept_deadline_epoch:signature
    """
    deadline_epoch = _epoch_seconds(accept_deadline)
    brief_id_hex = str(brief_id)
    payload = f"{brief_id_hex}:{nonce}:{deadline_epoch}"
    signature = _sign_payload(payload)
    return f"{payload}:{signature}"


def parse_invite_token(token: str) -> tuple[UUID, str, int, str]:
    """Parse an invite token into its components.

    Returns:
        Tuple of (brief_id, nonce, accept_deadline_epoch, signature).

    Raises:
        APIError: If the token format is invalid.
    """
    parts = token.split(":")
    if len(parts) != 4:
        raise APIError(
            code="INVITE_INVALID_TOKEN",
            message="Invalid invite token format",
            status_code=401,
        )

    brief_id_hex, nonce, deadline_str, signature = parts
    try:
        brief_id = UUID(brief_id_hex)
        accept_deadline_epoch = int(deadline_str)
    except (ValueError, AttributeError) as exc:
        raise APIError(
            code="INVITE_INVALID_TOKEN",
            message="Invalid invite token format",
            status_code=401,
        ) from exc

    return brief_id, nonce, accept_deadline_epoch, signature


def verify_invite_token_signature(token: str) -> tuple[UUID, str, int]:
    """Verify the HMAC signature of an invite token.

    Returns:
        Tuple of (brief_id, nonce, accept_deadline_epoch).

    Raises:
        APIError: If the signature does not match.
    """
    brief_id, nonce, accept_deadline_epoch, signature = parse_invite_token(token)
    payload = f"{brief_id}:{nonce}:{accept_deadline_epoch}"
    expected_signature = _sign_payload(payload)

    try:
        if not hmac.compare_digest(expected_signature, signature):
            raise APIError(
                code="INVITE_INVALID_TOKEN",
                message="Invalid invite token signature",
                status_code=401,
            )
    except (TypeError, binascii.Error) as exc:
        raise APIError(
            code="INVITE_INVALID_TOKEN",
            message="Invalid invite token signature",
            status_code=401,
        ) from exc

    return brief_id, nonce, accept_deadline_epoch


def _now() -> datetime:
    return datetime.now(UTC)


def get_invite_by_token(session: Session, token: str) -> BriefInvite:
    """Validate an invite token and return the corresponding invite record.

    Validation order:
    1. HMAC signature check (no DB lookup).
    2. accept_deadline has not expired.
    3. Database lookup by nonce.
    4. Invite has not been invalidated.

    Raises:
        APIError: If any validation step fails.
    """
    _, nonce, accept_deadline_epoch = verify_invite_token_signature(token)

    if accept_deadline_epoch <= _epoch_seconds(_now()):
        raise APIError(
            code="INVITE_EXPIRED",
            message="Invite link has expired",
            status_code=410,
        )

    invite = (
        session.execute(select(BriefInvite).where(BriefInvite.nonce == nonce)).scalars().first()
    )

    if invite is None:
        raise APIError(
            code="INVITE_INVALID_TOKEN",
            message="Invite not found",
            status_code=401,
        )

    if invite.invalidated_at is not None:
        raise APIError(
            code="INVITE_INVALIDATED",
            message="Invite has been invalidated. Please log in to continue.",
            status_code=410,
        )

    return invite


def create_invite(
    session: Session,
    brief_id: UUID,
    from_user: UUID,
    recipient_name: str,
    recipient_email: str | None,
    recipient_phone: str | None,
    accept_deadline: datetime,
    complete_deadline: datetime,
    temporary_user_id: UUID,
) -> BriefInvite:
    """Create a BriefInvite record with a signed token.

    Args:
        session: SQLAlchemy database session.
        brief_id: UUID of the brief being sent.
        from_user: UUID of the sender.
        recipient_name: Display name of the recipient.
        recipient_email: Optional email of the recipient.
        recipient_phone: Optional phone of the recipient.
        accept_deadline: Deadline for accepting or rejecting the invite.
        complete_deadline: Deadline for completing the brief.
        temporary_user_id: UUID of the temporary user assigned to the brief.

    Returns:
        The created BriefInvite record.
    """
    nonce = _generate_nonce()
    token = generate_invite_token(brief_id, nonce, accept_deadline)

    invite = BriefInvite(
        id=uuid4(),
        brief_id=brief_id,
        nonce=nonce,
        token=token,
        name=recipient_name,
        temporary_user_id=temporary_user_id,
        from_user=from_user,
        accept_deadline=accept_deadline,
        complete_deadline=complete_deadline,
        invalidated_at=None,
    )
    session.add(invite)
    session.flush()
    return invite


def invalidate_invite_for_brief(
    session: Session,
    brief_id: UUID,
    final_user_id: UUID,
) -> BriefInvite | None:
    """Mark the active invite for a brief as invalidated and record final user.

    Returns:
        The invalidated invite record, or None if no active invite exists.
    """
    now = _now()
    invite = (
        session.execute(
            select(BriefInvite).where(
                BriefInvite.brief_id == brief_id,
                BriefInvite.invalidated_at.is_(None),
            )
        )
        .scalars()
        .first()
    )

    if invite is not None:
        invite.invalidated_at = now
        invite.final_user_id = final_user_id

    return invite


def invalidate_invites_for_temporary_user(
    session: Session,
    temporary_user_id: UUID,
    final_user_id: UUID,
) -> None:
    """Mark all valid invites for a temporary user as invalidated and record final user."""
    now = _now()
    invites = (
        session.execute(
            select(BriefInvite).where(
                BriefInvite.temporary_user_id == temporary_user_id,
                BriefInvite.invalidated_at.is_(None),
            )
        )
        .scalars()
        .all()
    )

    for invite in invites:
        invite.invalidated_at = now
        invite.final_user_id = final_user_id


def get_invite_by_brief_id(session: Session, brief_id: UUID) -> BriefInvite | None:
    """Return the active invite for a brief, or None if not found."""
    return (
        session.execute(
            select(BriefInvite).where(
                BriefInvite.brief_id == brief_id,
                BriefInvite.invalidated_at.is_(None),
            )
        )
        .scalars()
        .first()
    )


def build_invite_url(token: str) -> str:
    """Return the relative invite URL for a token."""
    return f"/invites/{token}"
