"""Unit tests for Brief data models."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from briefchain.models import Brief, BriefStatus, BriefVersion


def test_insert_three_briefs_and_list_chain(db_session) -> None:
    """Insert a root brief plus two children and query the chain list."""
    upstream_id = uuid4()
    downstream_id = uuid4()

    root = Brief(
        brief_id=uuid4(),
        root_id=None,  # type: ignore[arg-type]
        parent_id=None,
        is_root=True,
        status=BriefStatus.ACCEPTED,
        created_by=upstream_id,
        assigned_to=None,
    )
    # Root references itself.
    root.root_id = root.brief_id

    child_one = Brief(
        brief_id=uuid4(),
        root_id=root.brief_id,
        parent_id=root.brief_id,
        is_root=False,
        status=BriefStatus.DRAFT,
        created_by=downstream_id,
        assigned_to=None,
    )
    child_two = Brief(
        brief_id=uuid4(),
        root_id=root.brief_id,
        parent_id=root.brief_id,
        is_root=False,
        status=BriefStatus.DRAFT,
        created_by=downstream_id,
        assigned_to=None,
    )

    # Create initial versions for each brief.
    for brief in (root, child_one, child_two):
        version = BriefVersion(
            brief_id=brief.brief_id,
            version=1,
            title=f"Brief {brief.brief_id}",
            content="Test content",
            modified_by=brief.created_by,
        )
        db_session.add(version)

    db_session.add_all([root, child_one, child_two])
    db_session.commit()

    result = (
        db_session.execute(
            select(Brief).where(Brief.root_id == root.brief_id).order_by(Brief.created_at)
        )
        .scalars()
        .all()
    )

    assert len(result) == 3
    assert result[0].is_root is True
    assert result[1].parent_id == root.brief_id
    assert result[2].parent_id == root.brief_id


def test_brief_status_enum_rejects_invalid_value() -> None:
    """BriefStatus enum rejects values outside the defined set."""
    with pytest.raises(ValueError):  # noqa: PT011
        BriefStatus("invalid")


def test_brief_version_composite_key(db_session) -> None:
    """A brief can have multiple versions with a composite primary key."""
    upstream_id = uuid4()
    brief_id = uuid4()

    brief = Brief(
        brief_id=brief_id,
        root_id=brief_id,
        parent_id=None,
        is_root=True,
        status=BriefStatus.DRAFT,
        created_by=upstream_id,
    )
    v1 = BriefVersion(
        brief_id=brief_id,
        version=1,
        title="Version 1",
        content="Initial",
        modified_by=upstream_id,
    )
    v2 = BriefVersion(
        brief_id=brief_id,
        version=2,
        title="Version 2",
        content="Updated",
        modified_by=upstream_id,
    )

    db_session.add_all([brief, v1, v2])
    db_session.commit()

    versions = (
        db_session.execute(select(BriefVersion).where(BriefVersion.brief_id == brief_id))
        .scalars()
        .all()
    )
    assert len(versions) == 2
