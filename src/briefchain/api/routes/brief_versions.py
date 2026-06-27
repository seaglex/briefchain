"""Brief version routes for the BriefChain API."""

from uuid import UUID

from fastapi import APIRouter

from briefchain.api.dependencies import SessionDep
from briefchain.api.services import briefs as brief_service

router = APIRouter(prefix="/briefs", tags=["brief-versions"])


@router.get("/{brief_id}/versions")
def list_versions(
    session: SessionDep,
    brief_id: UUID,
) -> list[dict]:
    """List all versions of a brief."""
    return brief_service.list_brief_versions(session, brief_id)
