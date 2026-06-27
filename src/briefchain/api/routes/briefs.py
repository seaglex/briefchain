"""Brief routes for the BriefChain API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from briefchain.api.dependencies import CurrentUserIdDep, SessionDep
from briefchain.api.schemas.briefs import (
    BriefCreateRequest,
    BriefDetail,
    BriefLifecycleResponse,
    BriefPatchRequest,
    BriefReviewRequest,
    BriefUpdateActionRequest,
    DownstreamActionRequest,
    RejectTransferRequest,
    SendBriefRequest,
    UpstreamActionRequest,
)
from briefchain.api.services import briefs as brief_service
from briefchain.models.enums import BriefDownstreamState, BriefUpstreamState

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.post("", response_model=BriefDetail, status_code=status.HTTP_201_CREATED)
def create_brief(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    request: BriefCreateRequest,
) -> BriefDetail:
    """Create a new brief."""
    return brief_service.create_brief(session, user_id, request)


@router.get("")
def list_briefs(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    role: Annotated[str, Query(pattern="^(created|assigned|all)$")] = "all",
    upstream_state: Annotated[BriefUpstreamState | None, Query()] = None,
    downstream_state: Annotated[BriefDownstreamState | None, Query()] = None,
    root_id: Annotated[UUID | None, Query()] = None,
    page_cursor: Annotated[str | None, Query()] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """List briefs with optional filters and cursor pagination."""
    return brief_service.list_briefs(
        session,
        user_id,
        role=role,
        upstream_state=upstream_state,
        downstream_state=downstream_state,
        root_id=root_id,
        page_cursor=page_cursor,
        page_size=page_size,
    )


@router.get("/{brief_id}", response_model=BriefDetail)
def get_brief(
    session: SessionDep,
    brief_id: UUID,
    version: Annotated[int | None, Query()] = None,
) -> BriefDetail:
    """Get a brief with its latest or requested version content."""
    return brief_service.get_brief_detail(session, brief_id, version_number=version)


@router.post("/{brief_id}/editing", response_model=BriefDetail)
def editing_action(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    action: Annotated[str, Query(pattern="^(patch|review)$")],
    request: BriefPatchRequest | BriefReviewRequest | None = None,
) -> BriefDetail:
    """Perform an editing-phase action on a brief."""
    if action == "patch":
        if request is None or not isinstance(request, BriefPatchRequest):
            raise brief_service.APIError(
                code="INVALID_REQUEST",
                message="PATCH request body required",
                status_code=422,
            )
        return brief_service.patch_brief(session, brief_id, user_id, request)

    if request is None:
        request = BriefReviewRequest()
    return brief_service.review_brief(session, brief_id, user_id, request)


@router.post("/{brief_id}/transfer", response_model=BriefLifecycleResponse)
def transfer_action(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    action: Annotated[str, Query(pattern="^(send|accept|reject)$")],
    request: SendBriefRequest | RejectTransferRequest | None = None,
) -> BriefLifecycleResponse:
    """Perform a transfer-phase action on a brief."""
    if action == "send":
        if request is None or not isinstance(request, SendBriefRequest):
            raise brief_service.APIError(
                code="INVALID_REQUEST",
                message="Send request body required",
                status_code=422,
            )
        return brief_service.send_brief(session, brief_id, user_id, request)
    if action == "accept":
        return brief_service.accept_brief(session, brief_id, user_id)

    if request is None or not isinstance(request, RejectTransferRequest):
        raise brief_service.APIError(
            code="INVALID_REQUEST",
            message="Reject reason required",
            status_code=422,
        )
    return brief_service.reject_brief(session, brief_id, user_id, request.reason)


@router.post("/{brief_id}/upstream-actions", response_model=BriefLifecycleResponse)
def upstream_action(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    action: Annotated[
        str,
        Query(pattern="^(cancel|suspend|resume|approve|reject_submit|update)$"),
    ],
    request: UpstreamActionRequest | BriefUpdateActionRequest | None = None,
) -> BriefLifecycleResponse:
    """Perform an upstream action on a brief."""
    if action == "update":
        if request is None or not isinstance(request, BriefUpdateActionRequest):
            raise brief_service.APIError(
                code="INVALID_REQUEST",
                message="Update request body required",
                status_code=422,
            )
        return brief_service.update_brief_version(session, brief_id, user_id, request)

    if request is None or not isinstance(request, UpstreamActionRequest):
        raise brief_service.APIError(
            code="INVALID_REQUEST",
            message="Action content required",
            status_code=422,
        )

    match action:
        case "cancel":
            return brief_service.cancel_brief(session, brief_id, user_id, request.content)
        case "suspend":
            return brief_service.suspend_brief(session, brief_id, user_id, request.content)
        case "resume":
            return brief_service.resume_brief(session, brief_id, user_id, request.content)
        case "approve":
            return brief_service.approve_brief(session, brief_id, user_id, request.content)
        case "reject_submit":
            return brief_service.reject_submit_brief(session, brief_id, user_id, request.content)

    raise brief_service.APIError(
        code="INVALID_ACTION",
        message=f"Unsupported upstream action: {action}",
        status_code=400,
    )


@router.post("/{brief_id}/downstream-actions", response_model=BriefLifecycleResponse)
def downstream_action(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    brief_id: UUID,
    action: Annotated[
        str,
        Query(pattern="^(process|submit|open|delegate|block)$"),
    ],
    request: DownstreamActionRequest | None = None,
) -> BriefLifecycleResponse:
    """Perform a downstream action on a brief."""
    if request is None:
        request = DownstreamActionRequest()

    match action:
        case "process":
            feedback = brief_service.downstream_process(
                session, brief_id, user_id, request.content, request.attachments
            )
            brief = brief_service.get_brief_detail(session, brief_id)
            return BriefLifecycleResponse(brief=brief, feedback=feedback)
        case "submit":
            if not request.content:
                raise brief_service.APIError(
                    code="INVALID_REQUEST",
                    message="Submit content required",
                    status_code=422,
                )
            return brief_service.downstream_submit(
                session, brief_id, user_id, request.content, request.attachments
            )
        case "open":
            if not request.content:
                raise brief_service.APIError(
                    code="INVALID_REQUEST",
                    message="Open reason required",
                    status_code=422,
                )
            return brief_service.downstream_open(session, brief_id, user_id, request.content)
        case "delegate":
            return brief_service.downstream_delegate(session, brief_id, user_id, request.content)
        case "block":
            if not request.content:
                raise brief_service.APIError(
                    code="INVALID_REQUEST",
                    message="Block reason required",
                    status_code=422,
                )
            return brief_service.downstream_block(
                session, brief_id, user_id, request.content, request.attachments
            )

    raise brief_service.APIError(
        code="INVALID_ACTION",
        message=f"Unsupported downstream action: {action}",
        status_code=400,
    )
