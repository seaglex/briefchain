"""Business logic service for brief-related operations."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
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
    BriefPatchRequest,
    BriefReviewRequest,
    BriefTransferResponse,
    BriefUpdateActionRequest,
    SendBriefRequest,
    UserSnapshot,
)
from briefchain.models import (
    Brief,
    BriefArbiterReview,
    BriefChain,
    BriefInvite,
    BriefTransferHistory,
    BriefVersion,
    Feedback,
    User,
)
from briefchain.models.enums import (
    ArbiterReviewStatus,
    BriefDownstreamState,
    BriefType,
    BriefUpstreamState,
    BriefVersionStatus,
    FeedbackType,
    UserType,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _encode_cursor(data: dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")


def _decode_cursor(cursor: str) -> dict[str, Any]:
    padding = 4 - len(cursor) % 4
    return json.loads(base64.urlsafe_b64decode(cursor + "=" * padding).decode())


def _parse_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    # Handle trailing Z for UTC.
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _format_time(value: datetime) -> str:
    return value.isoformat()


def _load_user(session: Session, user_id: UUID) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise APIError(
            code="USER_NOT_FOUND",
            message="User not found",
            status_code=404,
        )
    return user


def _user_snapshot(user: User | None) -> UserSnapshot | None:
    if user is None:
        return None
    return UserSnapshot(id=user.id, name=user.name)


def _current_version(brief: Brief) -> BriefVersion | None:
    """Return the version matching current_version, or the latest version if none final."""
    if not brief.versions:
        return None
    if brief.current_version is not None:
        for version in brief.versions:
            if version.version == brief.current_version:
                return version
    return brief.versions[-1]


def _latest_unfinalized_version(brief: Brief) -> BriefVersion | None:
    """Return the most recent unfinalized version (draft or reviewed), if any."""
    for version in reversed(brief.versions):
        if version.status in {BriefVersionStatus.DRAFT, BriefVersionStatus.REVIEWED}:
            return version
    return None


def _unfinalized_version_number(brief: Brief) -> int | None:
    """Return the editable unfinalized version number, or None if no unfinalized version exists."""
    unfinalized = _latest_unfinalized_version(brief)
    return unfinalized.version if unfinalized is not None else None


def _max_version(brief: Brief) -> int:
    return max((v.version for v in brief.versions), default=0)


def _sync_brief_from_version(
    session: Session,
    brief: Brief,
    version: BriefVersion,
    state_changed_by: UUID | None = None,
) -> None:
    """Synchronize denormalized brief fields from a final version."""
    brief.title = version.title
    brief.type = version.type
    brief.priority = version.priority
    brief.expected_completion_at = version.expected_completion_at
    if state_changed_by is not None:
        user = _load_user(session, state_changed_by)
        brief.status_changed_by = state_changed_by
        brief.status_changed_by_name = user.name
        brief.status_changed_at = _now()


def _set_state_changed(session: Session, brief: Brief, user_id: UUID) -> None:
    user = _load_user(session, user_id)
    brief.status_changed_by = user_id
    brief.status_changed_by_name = user.name
    brief.status_changed_at = _now()


def _create_feedback(
    session: Session,
    brief: Brief,
    from_user_id: UUID,
    to_user_id: UUID,
    feedback_type: FeedbackType,
    content: str,
    attachments: list[dict],
    is_to_down: bool,
) -> Feedback:
    """Create a feedback record with name snapshots."""
    from_user = _load_user(session, from_user_id)
    to_user = _load_user(session, to_user_id)
    feedback = Feedback(
        id=uuid4(),
        brief_id=brief.brief_id,
        brief_version=brief.current_version if brief.current_version is not None else 1,
        is_to_down=is_to_down,
        type=feedback_type,
        content=content,
        attachments=attachments,
        from_user=from_user_id,
        from_user_name=from_user.name,
        to_user=to_user_id,
        to_user_name=to_user.name,
        is_auto_generated=False,
        confirmed_at=None,
    )
    session.add(feedback)
    return feedback


def _serialize_brief(
    brief: Brief,
    version: BriefVersion | None = None,
    detail: bool = False,
) -> BriefListItem | BriefDetail:
    if version is None:
        version = _current_version(brief)

    title = brief.title
    brief_type = brief.type
    priority = brief.priority
    expected_completion = brief.expected_completion_at
    estimated = None
    content = ""
    attachments: list[dict] = []
    if version is not None:
        content = version.content
        attachments = version.attachments
        estimated = version.estimated_man_days
        if brief.current_version is None:
            # Before any version is final, denormalized fields come from v1.
            title = version.title
            brief_type = version.type
            priority = version.priority
            expected_completion = version.expected_completion_at

    current_version = brief.current_version
    version_number = version.version if version else (current_version or 1)
    is_current = (
        version is not None and current_version is not None and version.version == current_version
    )

    # Return the status of the version being returned. When no explicit version is
    # requested, `version` is already the current version, so this still reflects
    # the current version's status.
    current_version_status = version.status if version is not None else None

    base = BriefListItem(
        brief_id=brief.brief_id,
        title=title,
        type=brief_type,
        upstream_state=brief.upstream_state,
        downstream_state=brief.downstream_state,
        priority=priority,
        created_by_id=brief.created_by,
        created_by_name=brief.created_by_name,
        assigned_to_id=brief.assigned_to,
        assigned_to_name=brief.assigned_to_name,
        status_changed_by_id=brief.status_changed_by,
        status_changed_by_name=brief.status_changed_by_name,
        status_changed_at=_format_time(brief.status_changed_at),
        updated_at=_format_time(brief.updated_at),
    )

    if not detail:
        return base

    return BriefDetail(
        **base.model_dump(),
        root_id=brief.root_id,
        parent_id=brief.parent_id,
        content=content,
        attachments=attachments,
        current_version=current_version,
        current_version_status=current_version_status,
        version=version_number,
        is_current=is_current,
        unfinalized_version=_unfinalized_version_number(brief),
        estimated_man_days=float(estimated) if estimated is not None else None,
        expected_completion_at=_format_time(expected_completion) if expected_completion else None,
        created_at=_format_time(brief.created_at),
    )


def _serialize_transfer(
    transfer: BriefTransferHistory,
) -> BriefTransferResponse:
    return BriefTransferResponse(
        id=transfer.id,
        brief_version=transfer.brief_version,
        from_user_id=transfer.from_user,
        from_user_name=transfer.from_user_name,
        to_user_id=transfer.to_user,
        to_user_name=transfer.to_user_name,
        sent_at=_format_time(transfer.sent_at),
        accepted_at=_format_time(transfer.accepted_at) if transfer.accepted_at else None,
        rejected_at=_format_time(transfer.rejected_at) if transfer.rejected_at else None,
        rejection_reason=transfer.rejection_reason,
    )


def _serialize_feedback(feedback: Feedback) -> dict:
    return {
        "id": str(feedback.id),
        "brief_id": str(feedback.brief_id),
        "brief_version": feedback.brief_version,
        "is_to_down": feedback.is_to_down,
        "type": str(feedback.type),
        "content": feedback.content,
        "attachments": feedback.attachments,
        "from_user_id": str(feedback.from_user),
        "from_user_name": feedback.from_user_name,
        "to_user_id": str(feedback.to_user),
        "to_user_name": feedback.to_user_name,
        "is_auto_generated": feedback.is_auto_generated,
        "confirmed_at": _format_time(feedback.confirmed_at) if feedback.confirmed_at else None,
        "created_at": _format_time(feedback.created_at),
    }


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
    creator = _load_user(session, user_id)

    brief = Brief(
        brief_id=brief_id,
        root_id=brief_id,
        parent_id=request.parent_id,
        is_root=request.parent_id is None,
        current_version=None,
        upstream_state=BriefUpstreamState.EDITING,
        downstream_state=None,
        title=request.title,
        type=request.type,
        priority=request.priority,
        expected_completion_at=_parse_iso(request.expected_completion_at),
        created_by=user_id,
        created_by_name=creator.name,
        assigned_to=None,
        assigned_to_name=None,
        status_changed_by=user_id,
        status_changed_by_name=creator.name,
        status_changed_at=now,
    )
    session.add(brief)

    if brief.parent_id is not None:
        parent = _require_brief(session, brief.parent_id)
        brief.root_id = parent.root_id

    version = BriefVersion(
        brief_id=brief.brief_id,
        version=1,
        status=BriefVersionStatus.DRAFT,
        title=request.title,
        type=request.type,
        content=request.content,
        attachments=request.attachments,
        priority=request.priority,
        estimated_man_days=(
            Decimal(str(request.estimated_man_days))
            if request.estimated_man_days is not None
            else None
        ),
        expected_completion_at=_parse_iso(request.expected_completion_at),
        arbiter_review_id=None,
        is_upstream_changed=False,
        revision_reason="initial",
        modified_by=user_id,
        modified_by_name=creator.name,
        modified_at=now,
        change_summary="Initial version",
    )
    session.add(version)

    if brief.parent_id is None:
        chain = BriefChain(
            chain_id=brief.brief_id,
            title=request.title,
            owner_id=user_id,
            owner_name=creator.name,
            priority=request.priority,
        )
        session.add(chain)

    session.commit()
    session.refresh(brief)
    brief = _load_brief_with_versions(session, brief.brief_id)

    return _serialize_brief(brief, version=version, detail=True)


def list_briefs(
    session: Session,
    user_id: UUID,
    role: str = "all",
    upstream_state: BriefUpstreamState | None = None,
    downstream_state: BriefDownstreamState | None = None,
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

    if upstream_state is not None:
        conditions.append(Brief.upstream_state == upstream_state)
    if downstream_state is not None:
        conditions.append(Brief.downstream_state == downstream_state)
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

    items = [_serialize_brief(brief, detail=False) for brief in briefs]

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


def get_brief_detail(
    session: Session,
    brief_id: UUID,
    version_number: int | None = None,
) -> BriefDetail:
    """Return a brief with its latest or requested version content."""
    brief = _load_brief_with_versions(session, brief_id)
    version = None
    if version_number is not None:
        version = next((v for v in brief.versions if v.version == version_number), None)
        if version is None:
            raise APIError(
                code="VERSION_NOT_FOUND",
                message="Version not found",
                status_code=404,
            )

    return _serialize_brief(brief, version=version, detail=True)


def list_brief_versions(session: Session, brief_id: UUID) -> list[dict]:
    """Return all versions of a brief."""
    brief = _load_brief_with_versions(session, brief_id)

    return [
        {
            "version": version.version,
            "status": str(version.status),
            "title": version.title,
            "modified_by_id": version.modified_by,
            "modified_by_name": version.modified_by_name,
            "modified_at": _format_time(version.modified_at),
            "change_summary": version.change_summary,
            "is_upstream_changed": version.is_upstream_changed,
            "revision_reason": version.revision_reason,
        }
        for version in sorted(brief.versions, key=lambda v: v.version, reverse=True)
    ]


def patch_brief(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: BriefPatchRequest,
) -> BriefDetail:
    """Update an editable draft/reviewed version or create a new draft from a final version.

    This operation only touches version state; it does not modify the brief's
    upstream/downstream state or synchronize denormalized brief fields.
    """
    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)
    user = _load_user(session, user_id)

    now = _now()
    version = _latest_unfinalized_version(brief)
    if version is None:
        # All existing versions are final; fork a new draft from the current final version.
        current = _current_version(brief)
        if current is None:
            raise APIError(
                code="VERSION_NOT_FOUND",
                message="No editable version found",
                status_code=404,
            )
        next_version = current.version + 1
        if any(v.version == next_version for v in brief.versions):
            raise APIError(
                code="DRAFT_ALREADY_EXISTS",
                message="A draft version already exists for this brief",
                status_code=409,
            )
        version = BriefVersion(
            brief_id=brief.brief_id,
            version=next_version,
            status=BriefVersionStatus.DRAFT,
            title=current.title,
            type=current.type,
            content=current.content,
            attachments=current.attachments,
            priority=current.priority,
            estimated_man_days=current.estimated_man_days,
            expected_completion_at=current.expected_completion_at,
            is_upstream_changed=True,
            revision_reason=current.revision_reason,
            modified_by=user_id,
            modified_by_name=user.name,
            modified_at=now,
            change_summary=current.change_summary,
        )
        session.add(version)

    if request.title is not None:
        version.title = request.title
    if request.type is not None:
        version.type = request.type
    if request.content is not None:
        version.content = request.content
    if request.attachments is not None:
        version.attachments = request.attachments
    if request.priority is not None:
        version.priority = request.priority
    if request.estimated_man_days is not None:
        version.estimated_man_days = Decimal(str(request.estimated_man_days))
    if request.expected_completion_at is not None:
        version.expected_completion_at = _parse_iso(request.expected_completion_at)

    version.modified_by = user_id
    version.modified_by_name = user.name
    version.modified_at = now
    if request.revision_reason is not None:
        version.revision_reason = request.revision_reason
    if request.change_summary is not None:
        version.change_summary = request.change_summary

    # Editing a reviewed version invalidates the review; it must be re-submitted.
    if version.status == BriefVersionStatus.REVIEWED:
        version.status = BriefVersionStatus.DRAFT

    session.commit()
    session.refresh(brief)
    brief = _load_brief_with_versions(session, brief.brief_id)

    return _serialize_brief(brief, version=version, detail=True)


def review_brief(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: BriefReviewRequest | None = None,
) -> BriefDetail:
    """Submit the current draft version for review."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)

    version = _latest_unfinalized_version(brief)
    if version is None or version.status != BriefVersionStatus.DRAFT:
        raise APIError(
            code="INVALID_STATUS",
            message="Only a draft version can be submitted for review",
            status_code=409,
        )

    # MVP: auto-pass Arbiter review.
    review = BriefArbiterReview(
        id=uuid4(),
        brief_id=brief.brief_id,
        brief_version=version.version,
        arbiter_id="force_skip",
        status=ArbiterReviewStatus.FORCE_SKIPPED,
        score=None,
        issues=[],
        suggestions=[],
        reviewed_at=_now(),
    )
    session.add(review)
    session.flush()

    version.status = BriefVersionStatus.REVIEWED
    version.arbiter_review_id = review.id
    version.modified_at = _now()

    session.commit()
    session.refresh(brief)
    brief = _load_brief_with_versions(session, brief.brief_id)

    return _serialize_brief(brief, version=version, detail=True)


def send_brief(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: SendBriefRequest,
) -> BriefLifecycleResponse:
    """Send a reviewed or previously-final brief to a downstream user or external recipient."""
    from briefchain.api.services import invites as invite_service

    now = _now()
    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)

    version = _current_version(brief)
    if version is None or version.status not in (
        BriefVersionStatus.REVIEWED,
        BriefVersionStatus.FINAL,
    ):
        raise APIError(
            code="INVALID_STATUS",
            message="Only reviewed or final brief versions can be sent",
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

    assignee = _load_user(session, assigned_to)

    # Mark version as final and sync denormalized brief fields.
    if version.status == BriefVersionStatus.REVIEWED:
        version.status = BriefVersionStatus.FINAL
    version.modified_at = now
    brief.current_version = version.version
    _sync_brief_from_version(session, brief, version, state_changed_by=user_id)
    brief.upstream_state = BriefUpstreamState.SENT
    brief.downstream_state = None
    brief.assigned_to = assigned_to
    brief.assigned_to_name = assignee.name

    transfer = BriefTransferHistory(
        id=uuid4(),
        brief_id=brief.brief_id,
        brief_version=brief.current_version,
        arbiter_review_id=version.arbiter_review_id,
        from_user=user_id,
        from_user_name=_load_user(session, user_id).name,
        to_user=assigned_to,
        to_user_name=assignee.name,
        sent_at=now,
    )
    session.add(transfer)
    session.commit()

    brief = _load_brief_with_versions(session, brief_id)
    transfer = session.get(BriefTransferHistory, transfer.id)

    response = BriefLifecycleResponse(
        brief=_serialize_brief(brief, detail=True),
        transfer=_serialize_transfer(transfer),
    )

    if request.is_temporary_user and not is_internal_send:
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
        existing = (
            session.execute(
                select(User).where(
                    or_(
                        User.email == email if email else False,
                        User.phone == phone if phone else False,
                    )
                )
            )
            .scalars()
            .first()
        )

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
    invite = (
        session.execute(
            select(BriefInvite).where(
                BriefInvite.temporary_user_id == temporary_user_id,
                BriefInvite.final_user_id.isnot(None),
            )
        )
        .scalars()
        .first()
    )
    return invite.final_user_id if invite is not None else None


def accept_brief(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    note: str | None = None,
) -> BriefLifecycleResponse:
    """Accept a sent brief."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_assigned(brief, user_id)
    if brief.upstream_state != BriefUpstreamState.SENT:
        raise APIError(
            code="INVALID_STATUS",
            message="Only sent briefs can be accepted",
            status_code=409,
        )

    transfer = _latest_pending_transfer(session, brief_id)
    if transfer is not None:
        transfer.accepted_at = _now()
    brief.upstream_state = BriefUpstreamState.IN_PROCESS
    brief.downstream_state = BriefDownstreamState.OPENED
    _set_state_changed(session, brief, user_id)
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)

    return BriefLifecycleResponse(
        brief=_serialize_brief(brief, detail=True),
        transfer=_serialize_transfer(transfer) if transfer else None,
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
    if brief.upstream_state != BriefUpstreamState.SENT:
        raise APIError(
            code="INVALID_STATUS",
            message="Only sent briefs can be rejected",
            status_code=409,
        )

    transfer = _latest_pending_transfer(session, brief_id)
    if transfer is not None:
        transfer.rejected_at = _now()
        transfer.rejection_reason = reason
    brief.upstream_state = BriefUpstreamState.EDITING
    brief.downstream_state = None
    brief.assigned_to = None
    brief.assigned_to_name = None
    _set_state_changed(session, brief, user_id)
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)

    return BriefLifecycleResponse(
        brief=_serialize_brief(brief, detail=True),
        transfer=_serialize_transfer(transfer) if transfer else None,
    )


def upstream_action(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    action: str,
    content: str,
) -> BriefLifecycleResponse:
    """Perform an upstream state-changing action on a brief (excluding update)."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)

    config = _UPSTREAM_ACTIONS[action]

    forbidden = config.get("forbidden_upstream_states")
    if forbidden and brief.upstream_state in forbidden:
        raise APIError(
            code="INVALID_STATUS",
            message=f"Cannot {action} a brief in {brief.upstream_state.value} state",
            status_code=409,
        )

    required_upstream = config.get("required_upstream_states")
    if required_upstream and brief.upstream_state not in required_upstream:
        states = ", ".join(s.value for s in required_upstream)
        raise APIError(
            code="INVALID_STATUS",
            message=f"Only briefs in {states} can be {action}ed",
            status_code=409,
        )

    required_downstream = config.get("required_downstream_states")
    if required_downstream and brief.downstream_state not in required_downstream:
        states = ", ".join(s.value for s in required_downstream)
        raise APIError(
            code="INVALID_STATUS",
            message=f"Only briefs with downstream state {states} can be {action}ed",
            status_code=409,
        )

    to_user_id = brief.assigned_to
    if config.get("to_user") == "assigned_or_creator":
        to_user_id = brief.assigned_to if brief.assigned_to else brief.created_by

    _create_feedback(
        session,
        brief,
        user_id,
        to_user_id,
        config["feedback_type"],
        content,
        [],
        is_to_down=True,
    )

    target_upstream = config.get("target_upstream_state")
    if target_upstream is not None:
        brief.upstream_state = target_upstream
    target_downstream = config.get("target_downstream_state")
    if target_downstream is not None:
        brief.downstream_state = target_downstream

    _set_state_changed(session, brief, user_id)
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)
    return BriefLifecycleResponse(brief=_serialize_brief(brief, detail=True))


def update_brief_version(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    request: BriefUpdateActionRequest,
) -> BriefLifecycleResponse:
    """Send an existing reviewed unfinalized version to downstream.

    The caller must first patch a new draft version and submit it for review;
    this action only promotes the reviewed version to final and reopens the
    brief for downstream.
    """
    brief = _load_brief_with_versions(session, brief_id)
    _require_creator(brief, user_id)
    user = _load_user(session, user_id)
    if brief.upstream_state not in (BriefUpstreamState.IN_PROCESS, BriefUpstreamState.SUSPENDED):
        raise APIError(
            code="INVALID_STATUS",
            message="Only in-process / suspended briefs can be updated",
            status_code=409,
        )

    unfinalized = next(
        (v for v in brief.versions if v.version == request.version),
        None,
    )
    if unfinalized is None:
        raise APIError(
            code="VERSION_NOT_FOUND",
            message="The requested version does not belong to this brief",
            status_code=404,
        )
    if unfinalized.status != BriefVersionStatus.REVIEWED:
        raise APIError(
            code="INVALID_STATUS",
            message="Only a reviewed version can be updated",
            status_code=409,
        )

    now = _now()

    # Apply optional field overrides from the request onto the reviewed version.
    if request.title is not None:
        unfinalized.title = request.title
    if request.type is not None:
        unfinalized.type = request.type
    if request.content is not None:
        unfinalized.content = request.content
    if request.attachments is not None:
        unfinalized.attachments = request.attachments
    if request.priority is not None:
        unfinalized.priority = request.priority
    if request.estimated_man_days is not None:
        unfinalized.estimated_man_days = Decimal(str(request.estimated_man_days))
    if request.expected_completion_at is not None:
        unfinalized.expected_completion_at = _parse_iso(request.expected_completion_at)
    if request.revision_reason:
        unfinalized.revision_reason = request.revision_reason
    if request.change_summary:
        unfinalized.change_summary = request.change_summary
    unfinalized.modified_by = user_id
    unfinalized.modified_by_name = user.name
    unfinalized.modified_at = now

    # Auto-review and auto-finalize the existing version (MVP).
    review = BriefArbiterReview(
        id=uuid4(),
        brief_id=brief.brief_id,
        brief_version=unfinalized.version,
        arbiter_id="force_skip",
        status=ArbiterReviewStatus.FORCE_SKIPPED,
        score=None,
        issues=[],
        suggestions=[],
        reviewed_at=now,
    )
    session.add(review)
    session.flush()

    unfinalized.status = BriefVersionStatus.FINAL
    unfinalized.arbiter_review_id = review.id
    brief.current_version = unfinalized.version
    _sync_brief_from_version(session, brief, unfinalized, state_changed_by=user_id)
    brief.downstream_state = BriefDownstreamState.OPENED

    _create_feedback(
        session,
        brief,
        user_id,
        brief.assigned_to,
        FeedbackType.UPDATE,
        request.content,
        [],
        is_to_down=True,
    )
    _set_state_changed(session, brief, user_id)
    session.commit()
    brief = _load_brief_with_versions(session, brief_id)
    return BriefLifecycleResponse(brief=_serialize_brief(brief, detail=True))


_UPSTREAM_ACTIONS: dict[str, dict[str, Any]] = {
    "cancel": {
        "forbidden_upstream_states": {BriefUpstreamState.DONE},
        "feedback_type": FeedbackType.CANCEL,
        "target_upstream_state": BriefUpstreamState.CANCELLED,
        "to_user": "assigned_or_creator",
    },
    "suspend": {
        "required_upstream_states": {BriefUpstreamState.IN_PROCESS},
        "feedback_type": FeedbackType.SUSPEND,
        "target_upstream_state": BriefUpstreamState.SUSPENDED,
        "to_user": "assigned_or_creator",
    },
    "resume": {
        "required_upstream_states": {BriefUpstreamState.SUSPENDED},
        "feedback_type": FeedbackType.RESUME,
        "target_upstream_state": BriefUpstreamState.IN_PROCESS,
        "to_user": "assigned_or_creator",
    },
    "approve": {
        "required_downstream_states": {BriefDownstreamState.SUBMITTED},
        "feedback_type": FeedbackType.APPROVE,
        "target_upstream_state": BriefUpstreamState.DONE,
        "to_user": "assigned",
    },
    "reject_submit": {
        "required_downstream_states": {BriefDownstreamState.SUBMITTED},
        "feedback_type": FeedbackType.REJECT_SUBMIT,
        "target_upstream_state": BriefUpstreamState.IN_PROCESS,
        "target_downstream_state": BriefDownstreamState.OPENED,
        "to_user": "assigned",
    },
}


_DOWNSTREAM_ACTIONS: dict[str, dict[str, Any]] = {
    "process": {
        "feedback_type": FeedbackType.PROGRESS,
        "downstream_state": None,
        "supports_attachments": True,
    },
    "submit": {
        "feedback_type": FeedbackType.SUBMIT,
        "downstream_state": BriefDownstreamState.SUBMITTED,
        "supports_attachments": True,
    },
    "open": {
        "feedback_type": FeedbackType.OPEN,
        "downstream_state": BriefDownstreamState.OPENED,
        "supports_attachments": False,
    },
    "delegate": {
        "feedback_type": FeedbackType.DELEGATE,
        "downstream_state": BriefDownstreamState.DELEGATED,
        "supports_attachments": False,
    },
    "block": {
        "feedback_type": FeedbackType.BLOCK,
        "downstream_state": BriefDownstreamState.BLOCKED,
        "supports_attachments": True,
    },
}


def downstream_action(
    session: Session,
    brief_id: UUID,
    user_id: UUID,
    action: str,
    content: str | None,
    attachments: list[dict] | None,
) -> BriefLifecycleResponse:
    """Perform a downstream state-changing action on a brief."""
    brief = _load_brief_with_versions(session, brief_id)
    _require_assigned(brief, user_id)

    allowed_upstream_states = {
        BriefUpstreamState.IN_PROCESS,
        BriefUpstreamState.SUSPENDED,
        BriefUpstreamState.CANCELLED,
        BriefUpstreamState.DONE,
    }
    if brief.upstream_state not in allowed_upstream_states:
        raise APIError(
            code="INVALID_STATUS",
            message="Downstream actions are only available after the brief is accepted",
            status_code=409,
        )

    config = _DOWNSTREAM_ACTIONS[action]
    feedback = _create_feedback(
        session,
        brief,
        user_id,
        brief.created_by,
        config["feedback_type"],
        content or "",
        attachments or [] if config["supports_attachments"] else [],
        is_to_down=False,
    )

    new_downstream_state = config["downstream_state"]
    if new_downstream_state is not None:
        brief.downstream_state = new_downstream_state
        _set_state_changed(session, brief, user_id)

    session.commit()
    brief = _load_brief_with_versions(session, brief_id)

    response_fields: dict[str, Any] = {"brief": _serialize_brief(brief, detail=True)}
    if action == "process":
        response_fields["feedback"] = _serialize_feedback(feedback)
    return BriefLifecycleResponse(**response_fields)


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
    return [_serialize_transfer(transfer) for transfer in transfers]


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

    items = [
        {
            "chain_id": chain.chain_id,
            "title": chain.title,
            "owner_id": chain.owner_id,
            "owner_name": chain.owner_name,
            "priority": chain.priority,
            "root_brief_id": chain.chain_id,
            "brief_count": brief_counts.get(chain.chain_id, 0),
            "created_at": _format_time(chain.created_at),
        }
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

    brief_map = {brief.brief_id: brief for brief in briefs}

    def build_tree(brief: Brief) -> BriefTreeNode:
        version = _current_version(brief)
        return BriefTreeNode(
            brief_id=brief.brief_id,
            title=brief.title if version is None else version.title,
            upstream_state=brief.upstream_state,
            downstream_state=brief.downstream_state,
            children=[
                build_tree(brief_map[child_id])
                for child_id in _children_ids(briefs, brief.brief_id)
            ],
        )

    return ChainDetail(
        chain_id=chain.chain_id,
        title=chain.title,
        owner_id=chain.owner_id,
        owner_name=chain.owner_name,
        priority=chain.priority,
        root_brief=_serialize_brief(root_brief, detail=False),
        tree=build_tree(root_brief),
    )


def _children_ids(briefs: list[Brief], parent_id: UUID) -> list[UUID]:
    return [brief.brief_id for brief in briefs if brief.parent_id == parent_id]
