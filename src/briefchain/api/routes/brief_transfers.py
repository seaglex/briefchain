"""Brief transfer history routes for the BriefChain API."""

from uuid import UUID

from fastapi import APIRouter, Depends

from briefchain.api.dependencies import SessionDep, get_current_user_id
from briefchain.api.schemas.briefs import BriefTransferResponse
from briefchain.api.services import briefs as brief_service

router = APIRouter(
    prefix="/briefs",
    tags=["brief-transfers"],
    dependencies=[Depends(get_current_user_id)],
)


@router.get("/{brief_id}/transfers")
def list_transfers(
    session: SessionDep,
    brief_id: UUID,
) -> list[BriefTransferResponse]:
    """List transfer history for a brief."""
    return brief_service.list_transfers(session, brief_id)
