"""Chain routes for the BriefChain API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from briefchain.api.dependencies import CurrentUserIdDep, SessionDep
from briefchain.api.schemas.chains import ChainDetail
from briefchain.api.services import briefs as brief_service

router = APIRouter(prefix="/chains", tags=["chains"])


@router.get("")
def list_chains(
    session: SessionDep,
    user_id: CurrentUserIdDep,
    page_cursor: Annotated[str | None, Query()] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """List brief chains."""
    return brief_service.list_chains(
        session,
        user_id,
        page_cursor=page_cursor,
        page_size=page_size,
    )


@router.get("/{chain_id}", response_model=ChainDetail)
def get_chain(
    session: SessionDep,
    chain_id: UUID,
) -> ChainDetail:
    """Get chain detail with root brief and tree structure."""
    return brief_service.get_chain_detail(session, chain_id)
