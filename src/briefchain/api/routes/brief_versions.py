"""Brief version routes for the BriefChain API."""

from uuid import UUID

from fastapi import APIRouter

from briefchain.api.dependencies import SessionDep
from briefchain.api.schemas.briefs import BriefVersionDetail, BriefVersionListItem
from briefchain.api.services import briefs as brief_service

router = APIRouter(prefix="/briefs", tags=["brief-versions"])


@router.get("/{brief_id}/versions")
def list_versions(
    session: SessionDep,
    brief_id: UUID,
) -> list[BriefVersionListItem]:
    """List all versions of a brief."""
    return brief_service.list_brief_versions(session, brief_id)


@router.get("/{brief_id}/versions/{version}", response_model=BriefVersionDetail)
def get_version(
    session: SessionDep,
    brief_id: UUID,
    version: int,
) -> BriefVersionDetail:
    """Get a specific version of a brief."""
    return brief_service.get_brief_version(session, brief_id, version)
