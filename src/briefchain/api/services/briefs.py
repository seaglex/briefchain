"""Business logic service for brief-related operations."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from briefchain.api.exceptions import APIError
from briefchain.api.schemas.briefs import (
    BriefCreateRequest,
    BriefDetail,
    BriefLifecycleResponse,
    BriefListItem,
    BriefTransferResponse,
    BriefUpdateRequest,
    BriefVersionDetail,
    BriefVersionListItem,
    SendBriefRequest,
    UserRef,
)
from briefchain.models import (
    Brief,
    BriefChain,
    BriefInvite,
    BriefTransferHistory,
    BriefVersion,
    User,
)
from briefchain.models.enums import BriefPriority, BriefStatus, UserType


def _now() -> datetime:
    return datetime.now(UTC)


def _encode_cursor(data: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")


def _decode_cursor(cursor: str) -> dict[str, Any]:
    padding = 4 - len(cursor) % 4
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * padding).decode())


def _load_user_map(session: Session, user_ids: set[UUID]) -> dict[UUID, User]:
    if not user_ids:
        return {}
    users = session.execute(select(User).where(User.id.in_(list(user_ids)))).scalars().all()
    return {user.id: user for user in users}


def _user_ref(user: User | None) -> UserRef | None:
    if user is None:
        return None
    return UserRef(id=user.id, name=user.name)


def _format_time(value: datetime) -> str:
    return value.isoformat()


def _serialize_brief(
    brief: Brief,
    users: dict[UUID, User],
    version: BriefVersion | None = None,
    detail: bool = False,
) -> BriefListItem | BriefDetail:
    creator = users.get(brief.created_by)
    assignee = users.get(brief.assigned_to) if brief.assigned_to else None

    current_version = brief.current_version
    if version is None:
        version = next(
            (v for v in brief.versions if v.version == current_version),
            brief.versions[-1] if brief.versions else None,
        )

    title = version.title if version else ""
    priority = version.priority if version else BriefPriority.P2
    estimated = version.estimated_man_days if version else None

    base = BriefListItem(
        brief_id=brief.brief_id,
        title=title,
        status=brief.status,
        priority=priority,
        created_by=_user_ref(creator),
        assigned_to=_user_ref(assignee),
        updated_at=_format_time(brief.updated_at),
    )

    if not detail:
        return base

    return BriefDetail(
        **base.model_dump(),
        root_id=brief.root_id,
        parent_id=brief.parent_id,
        content=version.content if version else "",
        attachments=version.attachments if version else [],
        current_version=current_version,
        version=version.version if version else current_version,
        is_current=(version is not None and version.version == current_version),
        estimated_man_days=estimated,
        created_at=_format_time(brief.created_at),
    )


def _serialize_transfer(
    transfer: BriefTransferHistory,
    users: dict[UUID, User],
) -> BriefTransferResponse:
    return BriefTransferResponse(
        id=transfer.id,
        brief_version=transfer.brief_version,
        from_user=_user_ref(users.get(transfer.from_user)),
        to_user=_user_ref(users.get(transfer.to_user)),
        sent_at=_format_time(transfer.sent_at),
        accepted_at=_format_time(transfer.accepted_at) if transfer.accepted_at else None,
        rejected_at=_format_time(transfer.rejected_at) if transfer.rejected_at else None,
        rejection_reason=transfer.rejection_reason,
    )


def _require_brief(session: Session, brief_id: UUID) -> Brief:
    brief = session.get(Brief, brief_id)
    if brief is None:
        raise APIError(
            code="BRIEF_NOT_FOUND",
            message="Brief not found",
            status_code=404,
        )
    return brief


def _require_creator(brief: Brief, user_id: UUID) -> None:
    if brief.created_by != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only the creator can perform this action",
            status_code=403,
        )


def _require_creator_or_assigned(brief: Brief, user_id: UUID) -> None:
    if brief.created_by != user_id and brief.assigned_to != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only the creator or assigned user can perform this action",
            status_code=403,
        )


def _require_assigned(brief: Brief, user_id: UUID) -> None:
    if brief.assigned_to != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only the assigned user can perform this action",
            status_code=403,
        )


def _require_participant(brief: Brief, user_id: UUID) -> None:
    if brief.created_by != user_id and brief.assigned_to != user_id:
        raise APIError(
            code="FORBIDDEN",
            message="Only participants can perform this action",
            status_code=403,
        )


def _load_brief_with_versions(session: Session, brief_id: UUID) -> Brief:
    brief = session.execute(
        select(Brief).where(Brief.brief_id == brief_id).options(selectinload(Brief.versions))
    ).scalar_one_or_none()
    if brief is None:
        raise APIError(
            code="BRIEF_NOT_FOUND",
            message="Brief not found",
            status_code=404,
        )
    return brief


def create_brief(session: Session, user_id: UUID, request: BriefCreateRequest) -> BriefDetail:
    """Create a new root or child brief."""
    now = _now()
    brief_id = uuid4()
    brief = Brief(
        brief_id=brief_id,
        root_id=brief_id,
        parent_id=request.parent_id,
        is_root=request.parent_id is None,
        status=BriefStatus.DRAFT,
        current_version=1,
        created_by=user_id,
        assigned_to=None,
    )
    session.add(brief)

    if brief.parent_id is not None:
        parent = _require_brief(session, brief.parent_id)
        brief.root_id = parent.root_id

    version = BriefVersion(
        brief_id=brief.brief_id,
        version=1,
        title=request.title,
        content=request.content,
        attachments=request.attachments,
        priority=request.priority,
        estimated_man_days=request.estimated_man_days,
        is_upstream_changed=False,
        revision_reason="initial",
        modified_by=user_id,
        modified_at=now,
        change_summary="Initial version",
    )
    session.add(version)

    if brief.parent_id is None:
        chain = BriefChain(chain_id=brief.brief_id, title=request.title)
        session.add(chain)

    session.commit()
    session.refresh(brief)

    users = _load_user_map(session, {brief.created_by, brief.assigned_to} - {None})
    return _serialize_brief(brief, users, version=version, detail=True)


def list_briefs(
    session: Session,
    user_id: UUID,
    role: str = "all",
    status: BriefStatus | None = None,
    root_id: UUID | None = None,
    page_cursor: str | None = None,
    page_size: int = 20,
) -> dict:
    """Return a paginated list of briefs."""
    page_size = max(1, min(page_size, 100))

    conditions = []
    if role == "created":
        conditions.append(Brief.created_by == user_id)
    elif role == "assigned":
        conditions.append(Brief.assigned_to == user_id)
    elif role == "all":
        conditions.append(
            or_(
                Brief.created_by == user_id,
                Brief.assigned_to == user_id,
            )
        )

    if status is not None:
        conditions.append(Brief.status == status)
    if root_id is not None:
        conditions.append(Brief.root_id == root_id)

    last_updated_at = None
    last_brief_id = None
    if page_cursor:
        try:
            decoded = _decode_cursor(page_cursor)
            last_updated_at = datetime.fromisoformat(decoded["updated_at"])
            last_brief_id = UUID(decoded["brief_id"])
        except (ValueError, KeyError) as exc:
            raise APIError(
                code="INVALID_CURSOR",
                message="Invalid pagination cursor",
                status_code=400,
            ) from exc

    if last_updated_at and last_brief_id:
        conditions.append(
            or_(
                Brief.updated_at < last_updated_at,
                and_(
                    Brief.updated_at == last_updated_at,
                    Brief.brief_id < last_brief_id,
                ),
            )
        )

    stmt = (
        select(Brief)
        .where(and_(True, *conditions))
        .order_by(Brief.updated_at.desc(), Brief.brief_id.desc())
        .limit(page_size)
        .options(selectinload(Brief.versions))
    )
    briefs = session.execute(stmt).scalars().all()

    user_ids = {brief.created_by for brief in briefs}
    user_ids.update({brief.assigned_to for brief in briefs if brief.assigned_to})
    users = _load_user_map(session, user_ids)

    items = [_serialize_brief(brief, users, detail=False) for brief in briefs]

    next_cursor = None
    if len(briefs) == page_size:
        last = briefs[-1]
        next_cursor = _encode_cursor(
            {
                "updated_at": last.updated_at.isoformat(),
                "brief_id": str(last.brief_id),
            }
        )

    return {
        "briefs": items,
        "next_cursor": next_cursor,
    }


def get_brief_detail(session: Session, brief_id: UUID) -> BriefDetail:
    """Return a brief with its latest version content."""
    brief = _load_brief_with_versions(session, brief_id)
    users = _load_user_map(session, {brief.created_by, brief.assigned_to} - {None})
    return _serialize_brief(brief, users, detail=True)


def get_brief_version(session: Session, brief_id: UUID, version_number: int) -> BriefVersionDetail:
    """Return a specific version of a brief."""
    brief = _load_brief_with_versions(session, brief_id)
    version = next((v for v in brief.versions if v.version == version_number), None)
    if version is None:
        raise APIError(
            code="VERSION_NOT_FOUND",
            message="Version not found",
            status_code=404,
        )
    users = _load_user_map(
        session, {brief.created_by, brief.assigned_to, version.modified_by} - {None}
    )
    return _serialize_brief(brief, users, version=version, detail=True)


def list_brief_versions(session: Session, brief_id: UUID) -> list[BriefVersionListItem]:
    """Return all versions of a brief."""
    brief = _load_brief_with_versions(session, brief_id)
    user_ids = {version.modified_by for version in brief.versions}
    users = _load_user_map(session, user_ids)

    return [
        BriefVersionListItem(
            version=version.version,
            title=version.title,
            modified_by=_user_ref(users.get(version.modified_by)),
            modified_at=_format_time(version.modified_at),
            change_summary=version.change_summary,
            is_upstream_changed=version.is_upstream_changed,
            revision_reason=version.revision_reason,
        )
        for version in sorted(brief.versions, key=lambda v: v.version, reverse=True)
    ]


def update_brief(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: BriefUpdateRequest,
) -> BriefDetail:
    """Update a draft brief and create a new version."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)

    if brief.status != BriefStatus.DRAFT:
        raise APIError(
            code="INVALID_STATUS",
            message="Only draft briefs can be updated",
            status_code=409,
        )

    current_version = brief.versions[-1]
    new_version_number = brief.current_version + 1

    new_version = BriefVersion(
        brief_id=brief.brief_id,
        version=new_version_number,
        title=request.title if request.title is not None else current_version.title,
        content=request.content if request.content is not None else current_version.content,
        attachments=request.attachments
        if request.attachments is not None
        else current_version.attachments,
        priority=request.priority if request.priority is not None else current_version.priority,
        estimated_man_days=(
            request.estimated_man_days
            if request.estimated_man_days is not None
            else current_version.estimated_man_days
        ),
        is_upstream_changed=request.is_upstream_changed
        if request.is_upstream_changed is not None
        else False,
        revision_reason=request.revision_reason or "update",
        modified_by=user_id,
        modified_at=_now(),
        change_summary=request.change_summary or "Updated brief",
    )
    session.add(new_version)
    brief.current_version = new_version_number
    session.commit()
    session.refresh(brief)

    users = _load_user_map(
        session,
        {brief.created_by, brief.assigned_to, new_version.modified_by} - {None},
    )
    return _serialize_brief(brief, users, version=new_version, detail=True)


def submit_brief(session: Session, brief_id: UUID, user_id: UUID) -> BriefDetail:
    """Submit a draft brief for review."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)
    if brief.status != BriefStatus.DRAFT:
        raise APIError(
            code="INVALID_STATUS",
            message="Only draft briefs can be submitted",
            status_code=409,
        )
    brief.status = BriefStatus.REVIEWED
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)
    users = _load_user_map(session, {brief.created_by, brief.assigned_to} - {None})
    return _serialize_brief(brief, users, detail=True)


def send_brief(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: SendBriefRequest,
) -> BriefLifecycleResponse:
    """Send a reviewed brief to a downstream user or external recipient."""
    from briefchain.api.services import invites as invite_service

    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)
    if brief.status != BriefStatus.REVIEWED:
        raise APIError(
            code="INVALID_STATUS",
            message="Only reviewed briefs can be sent",
            status_code=409,
        )

    if request.is_temporary_user:
        assigned_to, is_internal_send = _resolve_temporary_recipient(
            session,
            brief_id,
            user_id,
            request,
        )
    else:
        if request.assigned_to is None:
            raise APIError(
                code="INVALID_SEND_REQUEST",
                message="assigned_to is required when is_temporary_user is false",
                status_code=422,
            )
        assigned_to = request.assigned_to
        is_internal_send = True

    transfer = BriefTransferHistory(
        id=uuid4(),
        brief_id=brief.brief_id,
        brief_version=brief.current_version,
        from_user=user_id,
        to_user=assigned_to,
        sent_at=_now(),
    )
    brief.status = BriefStatus.SENT
    brief.assigned_to = assigned_to
    session.add(transfer)
    session.commit()

    brief = _load_brief_with_versions(session, brief_id)
    transfer = session.get(BriefTransferHistory, transfer.id)

    users = _load_user_map(
        session,
        {brief.created_by, brief.assigned_to, transfer.from_user, transfer.to_user} - {None},
    )

    response = BriefLifecycleResponse(
        brief=_serialize_brief(brief, users, detail=True),
        transfer=_serialize_transfer(transfer, users),
    )

    if request.is_temporary_user and not is_internal_send:
        invite = session.execute(
            select(BriefInvite).where(
                BriefInvite.brief_id == brief_id,
                BriefInvite.invalidated_at.is_(None),
            )
        ).scalars().first()
        if invite is not None:
            response.invite = {
                "invite_url": invite_service.build_invite_url(invite.token),
                "accept_deadline": invite_service._format_time(invite.accept_deadline),
                "complete_deadline": invite_service._format_time(invite.complete_deadline),
            }

    return response


def _resolve_temporary_recipient(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: SendBriefRequest,
) -> tuple[UUID, bool]:
    """Resolve a temporary-user send request to a user UUID.

    Returns:
        Tuple of (assigned_to_user_id, is_internal_send). is_internal_send is True
        when the recipient is a registered user or a temporary user already linked
        to a final user; in that case no invite is created.
    """

    email = request.recipient_email.strip() if request.recipient_email else None
    phone = request.recipient_phone.strip() if request.recipient_phone else None

    if email or phone:
        existing = session.execute(
            select(User).where(
                or_(
                    User.email == email if email else False,
                    User.phone == phone if phone else False,
                )
            )
        ).scalars().first()

        if existing is not None:
            if existing.user_type == UserType.TEMPORARY:
                final_user_id = _get_final_user_id_for_temporary(session, existing.id)
                if final_user_id is not None:
                    return final_user_id, True
                # Reuse existing active temporary user; create a new invite for this brief.
                _create_invite_for_temporary_user(
                    session,
                    brief_id,
                    user_id,
                    request,
                    existing,
                )
                return existing.id, False
            return existing.id, True

    temporary_user = User(
        id=uuid4(),
        email=email,
        phone=phone,
        name=request.recipient_name or (email or phone or "Guest"),
        user_type=UserType.TEMPORARY,
        password_hash=None,
    )
    session.add(temporary_user)
    session.flush()

    _create_invite_for_temporary_user(
        session,
        brief_id,
        user_id,
        request,
        temporary_user,
    )
    return temporary_user.id, False


def _create_invite_for_temporary_user(
    session: Session,
    brief_id: UUID,
    from_user: UUID,
    request: SendBriefRequest,
    temporary_user: User,
) -> None:
    """Create a BriefInvite for a temporary user."""
    from briefchain.api.services import invites as invite_service

    now = _now()
    accept_deadline = now + timedelta(days=request.accept_deadline_days)
    complete_deadline = now + timedelta(days=request.complete_deadline_days)

    invite_service.create_invite(
        session=session,
        brief_id=brief_id,
        from_user=from_user,
        recipient_name=temporary_user.name,
        recipient_email=temporary_user.email,
        recipient_phone=temporary_user.phone,
        accept_deadline=accept_deadline,
        complete_deadline=complete_deadline,
        temporary_user_id=temporary_user.id,
    )


def _get_final_user_id_for_temporary(session: Session, temporary_user_id: UUID) -> UUID | None:
    """Return the final_user_id from any invite linked to the temporary user, if present."""
    invite = session.execute(
        select(BriefInvite).where(
            BriefInvite.temporary_user_id == temporary_user_id,
            BriefInvite.final_user_id.isnot(None),
        )
    ).scalars().first()
    return invite.final_user_id if invite is not None else None


def accept_brief(session: Session, brief_id: UUID, user_id: UUID) -> BriefLifecycleResponse:
    """Accept a sent brief."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_assigned(brief, user_id)
    if brief.status != BriefStatus.SENT:
        raise APIError(
            code="INVALID_STATUS",
            message="Only sent briefs can be accepted",
            status_code=409,
        )

    transfer = _latest_pending_transfer(session, brief_id)
    if transfer is not None:
        transfer.accepted_at = _now()
    brief.status = BriefStatus.ACCEPTED
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)

    users = _load_user_map(
        session,
        {
            brief.created_by,
            brief.assigned_to,
            transfer.from_user if transfer else None,
            transfer.to_user if transfer else None,
        }
        - {None},
    )
    return BriefLifecycleResponse(
        brief=_serialize_brief(brief, users, detail=True),
        transfer=_serialize_transfer(transfer, users) if transfer else None,
    )


def reject_brief(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    reason: str,
) -> BriefLifecycleResponse:
    """Reject a sent brief."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_assigned(brief, user_id)
    if brief.status != BriefStatus.SENT:
        raise APIError(
            code="INVALID_STATUS",
            message="Only sent briefs can be rejected",
            status_code=409,
        )

    transfer = _latest_pending_transfer(session, brief_id)
    if transfer is not None:
        transfer.rejected_at = _now()
        transfer.rejection_reason = reason
    brief.status = BriefStatus.DRAFT
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)

    users = _load_user_map(
        session,
        {
            brief.created_by,
            brief.assigned_to,
            transfer.from_user if transfer else None,
            transfer.to_user if transfer else None,
        }
        - {None},
    )
    return BriefLifecycleResponse(
        brief=_serialize_brief(brief, users, detail=True),
        transfer=_serialize_transfer(transfer, users) if transfer else None,
    )


def cancel_brief(session: Session, brief_id: UUID, user_id: UUID) -> BriefDetail:
    """Cancel a brief that is not done."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)
    if brief.status == BriefStatus.DONE:
        raise APIError(
            code="INVALID_STATUS",
            message="Done briefs cannot be cancelled",
            status_code=409,
        )
    brief.status = BriefStatus.CANCELLED
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)
    users = _load_user_map(session, {brief.created_by, brief.assigned_to} - {None})
    return _serialize_brief(brief, users, detail=True)


def complete_brief(session: Session, brief_id: UUID, user_id: UUID) -> BriefDetail:
    """Mark an accepted brief as done."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_assigned(brief, user_id)
    if brief.status != BriefStatus.ACCEPTED:
        raise APIError(
            code="INVALID_STATUS",
            message="Only accepted briefs can be completed",
            status_code=409,
        )
    brief.status = BriefStatus.DONE
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)
    users = _load_user_map(session, {brief.created_by, brief.assigned_to} - {None})
    return _serialize_brief(brief, users, detail=True)


def _latest_pending_transfer(session: Session, brief_id: UUID) -> BriefTransferHistory | None:
    return (
        session.execute(
            select(BriefTransferHistory)
            .where(
                BriefTransferHistory.brief_id == brief_id,
                BriefTransferHistory.accepted_at.is_(None),
                BriefTransferHistory.rejected_at.is_(None),
            )
            .order_by(BriefTransferHistory.sent_at.desc())
        )
        .scalars()
        .first()
    )


def list_transfers(session: Session, brief_id: UUID) -> list[BriefTransferResponse]:
    """Return transfer history for a brief."""
    _require_brief(session, brief_id)
    transfers = (
        session.execute(
            select(BriefTransferHistory)
            .where(BriefTransferHistory.brief_id == brief_id)
            .order_by(BriefTransferHistory.sent_at.desc())
        )
        .scalars()
        .all()
    )

    user_ids = set()
    for transfer in transfers:
        user_ids.add(transfer.from_user)
        user_ids.add(transfer.to_user)
    users = _load_user_map(session, user_ids)

    return [_serialize_transfer(transfer, users) for transfer in transfers]


def list_chains(
    session: Session,
    user_id: UUID,
    page_cursor: str | None = None,
    page_size: int = 20,
) -> dict:
    """Return a paginated list of chains."""
    page_size = max(1, min(page_size, 100))

    conditions = []
    last_created_at = None
    last_chain_id = None
    if page_cursor:
        try:
            decoded = _decode_cursor(page_cursor)
            last_created_at = datetime.fromisoformat(decoded["created_at"])
            last_chain_id = UUID(decoded["chain_id"])
        except (ValueError, KeyError) as exc:
            raise APIError(
                code="INVALID_CURSOR",
                message="Invalid pagination cursor",
                status_code=400,
            ) from exc

    if last_created_at and last_chain_id:
        conditions.append(
            or_(
                BriefChain.created_at < last_created_at,
                and_(
                    BriefChain.created_at == last_created_at,
                    BriefChain.chain_id < last_chain_id,
                ),
            )
        )

    stmt = (
        select(BriefChain)
        .where(and_(True, *conditions))
        .order_by(BriefChain.created_at.desc(), BriefChain.chain_id.desc())
        .limit(page_size)
    )
    chains = session.execute(stmt).scalars().all()

    chain_ids = [chain.chain_id for chain in chains]
    brief_counts = {}
    if chain_ids:
        counts = session.execute(
            select(Brief.root_id, func.count().label("cnt"))
            .where(Brief.root_id.in_(chain_ids))
            .group_by(Brief.root_id)
        ).all()
        brief_counts = {row.root_id: row.cnt for row in counts}

    from briefchain.api.schemas.chains import ChainListItem

    items = [
        ChainListItem(
            chain_id=chain.chain_id,
            title=chain.title,
            root_brief_id=chain.chain_id,
            brief_count=brief_counts.get(chain.chain_id, 0),
            created_at=_format_time(chain.created_at),
        )
        for chain in chains
    ]

    next_cursor = None
    if len(chains) == page_size:
        last = chains[-1]
        next_cursor = _encode_cursor(
            {
                "created_at": last.created_at.isoformat(),
                "chain_id": str(last.chain_id),
            }
        )

    return {
        "chains": items,
        "next_cursor": next_cursor,
    }


def get_chain_detail(session: Session, chain_id: UUID) -> dict:
    """Return chain detail with root brief and tree."""
    from briefchain.api.schemas.chains import BriefTreeNode, ChainDetail

    chain = session.get(BriefChain, chain_id)
    if chain is None:
        raise APIError(
            code="CHAIN_NOT_FOUND",
            message="Chain not found",
            status_code=404,
        )

    root_brief = _load_brief_with_versions(session, chain_id)
    briefs = (
        session.execute(
            select(Brief).where(Brief.root_id == chain_id).options(selectinload(Brief.versions))
        )
        .scalars()
        .all()
    )

    user_ids = {root_brief.created_by, root_brief.assigned_to}
    for brief in briefs:
        user_ids.add(brief.created_by)
        if brief.assigned_to:
            user_ids.add(brief.assigned_to)
    users = _load_user_map(session, user_ids)

    brief_map = {brief.brief_id: brief for brief in briefs}

    def build_tree(brief: Brief) -> BriefTreeNode:
        return BriefTreeNode(
            brief_id=brief.brief_id,
            title=brief.versions[-1].title if brief.versions else "",
            status=str(brief.status),
            children=[
                build_tree(brief_map[child_id])
                for child_id in _children_ids(briefs, brief.brief_id)
            ],
        )

    return ChainDetail(
        chain_id=chain.chain_id,
        title=chain.title,
        root_brief=_serialize_brief(root_brief, users, detail=False),
        tree=build_tree(root_brief),
    )


def _children_ids(briefs: list[Brief], parent_id: UUID) -> list[UUID]:
    return [brief.brief_id for brief in briefs if brief.parent_id == parent_id]
