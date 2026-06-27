"""Unit tests for Brief data models."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from briefchain.models import Brief, BriefUpstreamState, BriefVersion


def test_insert_three_briefs_and_list_chain(db_session) -> None:
    """Insert a root brief plus two children and query the chain list."""
    upstream_id = uuid4()
    downstream_id = uuid4()

    root = Brief(
        brief_id=uuid4(),
        root_id=None,  # type: ignore[arg-type]
        parent_id=None,
        is_root=True,
        upstream_state=BriefUpstreamState.IN_PROCESS,
        downstream_state=None,
        title="Root Brief",
        priority="p2",
        created_by=upstream_id,
        created_by_name="Upstream",
        assigned_to=None,
        assigned_to_name=None,
        status_changed_by=upstream_id,
        status_changed_by_name="Upstream",
        status_changed_at=datetime.now(UTC),
    )
    # Root references itself.
    root.root_id = root.brief_id

    child_one = Brief(
        brief_id=uuid4(),
        root_id=root.brief_id,
        parent_id=root.brief_id,
        is_root=False,
        upstream_state=BriefUpstreamState.EDITING,
        downstream_state=None,
        title="Child One",
        priority="p2",
        created_by=downstream_id,
        created_by_name="Downstream",
        assigned_to=None,
        assigned_to_name=None,
        status_changed_by=downstream_id,
        status_changed_by_name="Downstream",
        status_changed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )
    child_two = Brief(
        brief_id=uuid4(),
        root_id=root.brief_id,
        parent_id=root.brief_id,
        is_root=False,
        upstream_state=BriefUpstreamState.EDITING,
        downstream_state=None,
        title="Child Two",
        priority="p2",
        created_by=downstream_id,
        created_by_name="Downstream",
        assigned_to=None,
        assigned_to_name=None,
        status_changed_by=downstream_id,
        status_changed_by_name="Downstream",
        status_changed_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )

    # Create initial versions for each brief.
    for brief in (root, child_one, child_two):
        version = BriefVersion(
            brief_id=brief.brief_id,
            version=1,
            title=f"Brief {brief.brief_id}",
            content="Test content",
            modified_by=brief.created_by,
            modified_by_name=brief.created_by_name,
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


def test_brief_upstream_state_enum_rejects_invalid_value() -> None:
    """BriefUpstreamState enum rejects values outside the defined set."""
    with pytest.raises(ValueError):  # noqa: PT011
        BriefUpstreamState("invalid")


def test_brief_version_composite_key(db_session) -> None:
    """A brief can have multiple versions with a composite primary key."""
    upstream_id = uuid4()
    brief_id = uuid4()

    brief = Brief(
        brief_id=brief_id,
        root_id=brief_id,
        parent_id=None,
        is_root=True,
        upstream_state=BriefUpstreamState.EDITING,
        downstream_state=None,
        title="Versioned Brief",
        priority="p2",
        created_by=upstream_id,
        created_by_name="Creator",
        status_changed_by=upstream_id,
        status_changed_by_name="Creator",
        status_changed_at=datetime.now(UTC),
    )
    v1 = BriefVersion(
        brief_id=brief_id,
        version=1,
        title="Version 1",
        content="Initial",
        modified_by=upstream_id,
        modified_by_name="Creator",
    )
    v2 = BriefVersion(
        brief_id=brief_id,
        version=2,
        title="Version 2",
        content="Updated",
        modified_by=upstream_id,
        modified_by_name="Creator",
    )

    db_session.add_all([brief, v1, v2])
    db_session.commit()

    versions = (
        db_session.execute(select(BriefVersion).where(BriefVersion.brief_id == brief_id))
        .scalars()
        .all()
    )
    assert len(versions) == 2
