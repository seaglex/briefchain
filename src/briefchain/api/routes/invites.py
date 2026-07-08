"""Invite routes for the BriefChain API (public, token-based)."""

from fastapi import APIRouter, Body, Query

from briefchain.api.dependencies import InviteDep, SessionDep
from briefchain.api.schemas.briefs import (
    BriefLifecycleResponse,
    DownstreamActionRequest,
)
from briefchain.api.schemas.invites import (
    AcceptInviteRequest,
    RejectInviteRequest,
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


@router.post("/{token}/transfer", response_model=BriefLifecycleResponse)
def transfer_invite_action(
    invite: InviteDep,
    session: SessionDep,
    action: str = Query(pattern="^(accept|reject)$"),
    body: AcceptInviteRequest | RejectInviteRequest | None = None,
) -> BriefLifecycleResponse:
    """Accept or reject a sent brief using an invite token."""
    if action == "accept":
        if body is not None and isinstance(body, AcceptInviteRequest) and body.name:
            invite.temporary_user.name = body.name
            session.add(invite.temporary_user)
            session.commit()
        return brief_service.accept_brief(
            session,
            invite.brief_id,
            invite.temporary_user_id,
        )

    if body is None or not isinstance(body, RejectInviteRequest):
        raise brief_service.APIError(
            code="INVALID_REQUEST",
            message="Reject reason required",
            status_code=422,
        )
    return brief_service.reject_brief(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        body.reason,
    )


@router.post("/{token}/downstream-actions", response_model=BriefLifecycleResponse)
def downstream_invite_action(
    invite: InviteDep,
    session: SessionDep,
    action: str = Query(pattern="^(process|submit|open|delegate|block)$"),
    body: DownstreamActionRequest = Body(...),
) -> BriefLifecycleResponse:
    """Perform a downstream action on an in-process brief using an invite token."""
    return brief_service.downstream_action(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        action,
        body.content,
        body.attachments,
    )
