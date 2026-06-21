"""Tests for brief API endpoints."""

import pytest
from fastapi.testclient import TestClient

from briefchain.models import Brief

pytestmark = pytest.mark.usefixtures("jwt_secret")


def test_create_root_brief(client: TestClient, auth_headers_creator: dict[str, str]) -> None:
    """A creator can create a root brief."""
    response = client.post(
        "/api/v1/briefs",
        headers=auth_headers_creator,
        json={
            "title": "New Brief",
            "content": "Brief content",
            "priority": "p1",
            "estimated_man_days": 5.0,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Brief"
    assert data["status"] == "draft"
    assert data["current_version"] == 1
    assert data["is_current"] is True


def test_get_brief_latest_version(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """GET /briefs/:id returns the latest version."""
    response = client.get(f"/api/v1/briefs/{draft_brief.brief_id}", headers=auth_headers_creator)

    assert response.status_code == 200
    data = response.json()
    assert data["brief_id"] == str(draft_brief.brief_id)
    assert data["version"] == 1
    assert data["is_current"] is True


def test_update_brief_creates_new_version(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Updating a draft brief increments the version."""
    response = client.patch(
        f"/api/v1/briefs/{draft_brief.brief_id}",
        headers=auth_headers_creator,
        json={"title": "Updated Title"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_version"] == 2
    assert data["title"] == "Updated Title"


def test_submit_brief(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Creator can submit a draft brief."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/submit",
        headers=auth_headers_creator,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reviewed"


def test_send_brief(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
    downstream,
) -> None:
    """Creator can send a reviewed brief to downstream."""
    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/submit",
        headers=auth_headers_creator,
    )
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/send",
        headers=auth_headers_creator,
        json={"assigned_to": str(downstream.id)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["status"] == "sent"
    assert data["transfer"]["to_user"]["id"] == str(downstream.id)


def test_accept_brief(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    auth_headers_downstream: dict[str, str],
    draft_brief: Brief,
    downstream,
) -> None:
    """Downstream can accept a sent brief."""
    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/submit",
        headers=auth_headers_creator,
    )
    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/send",
        headers=auth_headers_creator,
        json={"assigned_to": str(downstream.id)},
    )

    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/accept",
        headers=auth_headers_downstream,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["status"] == "accepted"


def test_list_versions(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Versions endpoint lists all versions."""
    client.patch(
        f"/api/v1/briefs/{draft_brief.brief_id}",
        headers=auth_headers_creator,
        json={"title": "Updated"},
    )

    response = client.get(
        f"/api/v1/briefs/{draft_brief.brief_id}/versions",
        headers=auth_headers_creator,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_specific_version(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Specific version endpoint returns historical content."""
    client.patch(
        f"/api/v1/briefs/{draft_brief.brief_id}",
        headers=auth_headers_creator,
        json={"title": "Updated"},
    )

    response = client.get(
        f"/api/v1/briefs/{draft_brief.brief_id}/versions/1",
        headers=auth_headers_creator,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["is_current"] is False


def test_create_feedback(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Creator can create feedback on a brief."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/feedbacks",
        headers=auth_headers_creator,
        json={"type": "progress", "content": "Making progress"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "progress"
    assert data["content"] == "Making progress"


def test_list_chains(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Chains endpoint returns chains."""
    response = client.get("/api/v1/chains", headers=auth_headers_creator)

    assert response.status_code == 200
    data = response.json()
    assert len(data["chains"]) >= 1


def test_get_chain_detail(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Chain detail returns root brief and tree."""
    response = client.get(f"/api/v1/chains/{draft_brief.brief_id}", headers=auth_headers_creator)

    assert response.status_code == 200
    data = response.json()
    assert data["chain_id"] == str(draft_brief.brief_id)
    assert "tree" in data
