"""Pydantic schemas for chain endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from briefchain.api.schemas.briefs import BriefListItem
from briefchain.models.enums import BriefDownstreamState, BriefUpstreamState


class ChainListItem(BaseModel):
    """Chain list item response."""

    model_config = ConfigDict(from_attributes=True)

    chain_id: UUID
    title: str
    owner_id: UUID
    owner_name: str
    priority: str
    root_brief_id: UUID
    brief_count: int
    created_at: str


class BriefTreeNode(BaseModel):
    """Node in the brief tree structure."""

    model_config = ConfigDict(from_attributes=True)

    brief_id: UUID
    title: str
    upstream_state: BriefUpstreamState
    downstream_state: BriefDownstreamState | None
    children: list["BriefTreeNode"] = []


class ChainDetail(BaseModel):
    """Chain detail response with root brief and tree."""

    chain_id: UUID
    title: str
    owner_id: UUID
    owner_name: str
    priority: str
    root_brief: BriefListItem
    tree: BriefTreeNode
