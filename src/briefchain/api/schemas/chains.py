"""Pydantic schemas for chain endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from briefchain.api.schemas.briefs import BriefListItem


class ChainListItem(BaseModel):
    """Chain list item response."""

    model_config = ConfigDict(from_attributes=True)

    chain_id: UUID
    title: str
    root_brief_id: UUID
    brief_count: int
    created_at: str


class BriefTreeNode(BaseModel):
    """Node in the brief tree structure."""

    model_config = ConfigDict(from_attributes=True)

    brief_id: UUID
    title: str
    status: str
    children: list["BriefTreeNode"] = []


class ChainDetail(BaseModel):
    """Chain detail response with root brief and tree."""

    chain_id: UUID
    title: str
    root_brief: BriefListItem
    tree: BriefTreeNode
