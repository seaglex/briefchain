"""Invite routes for the BriefChain API (public, token-based)."""

from fastapi import APIRouter

from briefchain.api.dependencies import InviteDep, SessionDep
from briefchain.api.exceptions import APIError
from briefchain.api.schemas.briefs import BriefLifecycleResponse
from briefchain.api.schemas.feedbacks import FeedbackCreateRequest, FeedbackDetail
from briefchain.api.schemas.invites import (
    AcceptInviteRequest,
    BlockedInviteRequest,
    DoneInviteRequest,
    InviteViewResponse,
    RejectInviteRequest,
)
from briefchain.api.services import briefs as brief_service
from briefchain.api.services import feedbacks as feedback_service
from briefchain.api.services import invites as invite_service
from briefchain.models import Brief, BriefInvite, User
from briefchain.models.enums import BriefStatus, FeedbackType

router = APIRouter(prefix="/invites", tags=["invites"])


def _serialize_invite_metadata(invite: BriefInvite, sender_name: str) -> dict:
    """Return public invite metadata for responses."""
    return {
        "name": invite.name,
        "from_user": {"id": invite.from_user, "name": sender_name},
        "accept_deadline": invite_service._format_time(invite.accept_deadline),
        "complete_deadline": invite_service._format_time(invite.complete_deadline),
    }


@router.get("/{token}", response_model=InviteViewResponse)
def view_invite(
    invite: InviteDep,
    session: SessionDep,
) -> InviteViewResponse:
    """View an invite and the associated brief details."""
    sender = session.get(User, invite.from_user)
    sender_name = sender.name if sender is not None else ""
    brief = brief_service.get_brief_detail(session, invite.brief_id)
    return InviteViewResponse(
        invite=_serialize_invite_metadata(invite, sender_name),
        brief=brief,
    )


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


@router.post("/{token}/blocked", response_model=FeedbackDetail)
def block_invite(
    invite: InviteDep,
    session: SessionDep,
    body: BlockedInviteRequest,
) -> FeedbackDetail:
    """Mark an accepted brief as blocked using an invite token."""
    brief = session.get(Brief, invite.brief_id)
    if brief is None:
        raise APIError(
            code="BRIEF_NOT_FOUND",
            message="Brief not found",
            status_code=404,
        )
    if brief.status != BriefStatus.ACCEPTED:
        raise APIError(
            code="INVALID_STATUS",
            message="Only accepted briefs can be marked as blocked",
            status_code=409,
        )

    brief.status = BriefStatus.BLOCKED
    session.add(brief)

    feedback = feedback_service.create_feedback(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        FeedbackCreateRequest(
            type=FeedbackType.BLOCKED,
            content=body.reason,
            attachments=[],
        ),
    )
    return feedback


@router.post("/{token}/done", response_model=FeedbackDetail)
def done_invite(
    invite: InviteDep,
    session: SessionDep,
    body: DoneInviteRequest,
) -> FeedbackDetail:
    """Mark an accepted brief as done using an invite token."""
    brief_service.complete_brief(session, invite.brief_id, invite.temporary_user_id)

    feedback = feedback_service.create_feedback(
        session,
        invite.brief_id,
        invite.temporary_user_id,
        FeedbackCreateRequest(
            type=FeedbackType.COMPLETION,
            content=body.result,
            attachments=[],
        ),
    )
    return feedback
