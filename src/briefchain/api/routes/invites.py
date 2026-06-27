"""Invite routes for the BriefChain API (public, token-based)."""

from fastapi import APIRouter

from briefchain.api.dependencies import InviteDep, SessionDep
from briefchain.api.schemas.briefs import BriefDetail, BriefLifecycleResponse
from briefchain.api.schemas.invites import (
    AcceptInviteRequest,
    BlockInviteRequest,
    DelegateInviteRequest,
    OpenInviteRequest,
    RejectInviteRequest,
    SubmitInviteRequest,
)
from briefchain.api.services import briefs as brief_service
from briefchain.api.services import invites as invite_service
from briefchain.models import User

router = APIRouter(prefix="/invites", tags=["invites"])


def _serialize_invite_metadata(invite: InviteDep, sender_name: str) -> dict:
    """Return public invite metadata for responses."""
    return {
        "name": invite.name,
        "from_user": {"id": invite.from_user, "name": sender_name},
        "accept_deadline": invite_service._format_time(invite.accept_deadline),
        "complete_deadline": invite_service._format_time(invite.complete_deadline),
    }


@router.get("/{token}")
def view_invite(
    invite: InviteDep,
    session: SessionDep,
) -> dict:
    """View an invite and the associated brief details."""
    sender = session.get(User, invite.from_user)
    sender_name = sender.name if sender is not None else ""
    brief = brief_service.get_brief_detail(session, invite.brief_id)
    return {
        "invite": _serialize_invite_metadata(invite, sender_name),
        "brief": brief,
    }


@router.post("/{token}/accept", response_model=BriefLifecycleResponse)
def accept_invite(
    invite: InviteDep,
    session: SessionDep,
    body: AcceptInviteRequest | None = None,
) -> BriefLifecycleResponse:
    """Accept a sent brief using an invite token."""
    if body is not None and body.name:
        invite.temporary_user.name = body.name
        session.add(invite.temporary_user)
        session.commit()

    return brief_service.accept_brief(
        session,
        invite.brief_id,
        invite.temporary_user_id,
    )


@router.post("/{token}/reject", response_model=BriefLifecycleResponse)
def reject_invite(
    invite: InviteDep,
    session: SessionDep,
    body: RejectInviteRequest,
) -> BriefLifecycleResponse:
    """Reject a sent brief using an invite token."""
    return brief_service.reject_brief(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        body.reason,
    )


@router.post("/{token}/submit", response_model=BriefDetail)
def submit_invite(
    invite: InviteDep,
    session: SessionDep,
    body: SubmitInviteRequest,
) -> dict:
    """Submit completion of an accepted brief using an invite token."""
    return brief_service.downstream_submit(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        body.content,
        body.attachments,
    )


@router.post("/{token}/block", response_model=BriefDetail)
def block_invite(
    invite: InviteDep,
    session: SessionDep,
    body: BlockInviteRequest,
) -> dict:
    """Mark an in-process brief as blocked using an invite token."""
    return brief_service.downstream_block(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        body.reason,
        body.attachments,
    )


@router.post("/{token}/open", response_model=BriefDetail)
def open_invite(
    invite: InviteDep,
    session: SessionDep,
    body: OpenInviteRequest,
) -> dict:
    """Reopen a brief using an invite token."""
    return brief_service.downstream_open(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        body.reason,
    )


@router.post("/{token}/delegate", response_model=BriefDetail)
def delegate_invite(
    invite: InviteDep,
    session: SessionDep,
    body: DelegateInviteRequest | None = None,
) -> dict:
    """Mark a brief as delegated using an invite token."""
    content = body.content if body is not None else None
    return brief_service.downstream_delegate(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        content,
    )
