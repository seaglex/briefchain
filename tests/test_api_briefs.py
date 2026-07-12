"""Tests for brief API endpoints."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from briefchain.models import Brief, BriefArbiterReview, BriefVersion
from briefchain.models.enums import ArbiterReviewStatus, BriefVersionStatus

pytestmark = pytest.mark.usefixtures("jwt_secret")


def _complete_review_as_passed(db_session: Session, review_id: str) -> None:
    """Mark a processing review and its version as passed for test setup."""
    review = db_session.get(BriefArbiterReview, UUID(review_id))
    assert review is not None
    review.status = ArbiterReviewStatus.PASSED
    review.score = 80
    review.reviewed_at = datetime.now(UTC)

    version = db_session.get(BriefVersion, (review.brief_id, review.brief_version))
    if version is not None:
        version.status = BriefVersionStatus.REVIEWED
        version.arbiter_review_id = review.id

    db_session.commit()


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
    assert data["upstream_state"] == "editing"
    assert data["downstream_state"] is None
    assert data["current_version"] is None
    assert data["version"] == 1
    assert data["is_current"] is False


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
    assert data["is_current"] is False


def test_patch_brief_modifies_unfinalized_version(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Patching a never-finalized brief modifies the draft version in place."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=patch",
        headers=auth_headers_creator,
        json={"version": 1, "title": "Updated Title"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["current_version"] is None
    assert data["title"] == "Updated Title"
    assert data["version"] == 1


def test_review_brief(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Creator can submit a draft version for asynchronous review."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=submit-review",
        headers=auth_headers_creator,
        json={"version": 1},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["brief_id"] == str(draft_brief.brief_id)
    assert data["brief_version"] == 1
    assert data["status"] == "processing"


def test_send_brief(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
    downstream,
    db_session: Session,
) -> None:
    """Creator can send a reviewed brief to downstream."""
    review_response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=submit-review",
        headers=auth_headers_creator,
        json={"version": 1},
    )
    _complete_review_as_passed(db_session, review_response.json()["review_id"])

    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={"assigned_to": str(downstream.id)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["upstream_state"] == "sent"
    assert data["brief"]["current_version"] == 1
    assert data["transfer"]["to_user_id"] == str(downstream.id)


def test_resend_brief_after_rejection(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    auth_headers_downstream: dict[str, str],
    auth_headers_other_user: dict[str, str],
    draft_brief: Brief,
    downstream,
    other_user,
    db_session: Session,
) -> None:
    """Creator can resend a previously-final version after downstream rejection."""
    review_response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=submit-review",
        headers=auth_headers_creator,
        json={"version": 1},
    )
    _complete_review_as_passed(db_session, review_response.json()["review_id"])

    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={"assigned_to": str(downstream.id)},
    )

    reject_response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/transfer?action=reject",
        headers=auth_headers_downstream,
        json={"reason": "Not interested"},
    )
    assert reject_response.status_code == 200
    rejected = reject_response.json()
    assert rejected["brief"]["upstream_state"] == "editing"
    assert rejected["brief"]["assigned_to_id"] is None

    resend_response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={"assigned_to": str(other_user.id)},
    )

    assert resend_response.status_code == 200
    data = resend_response.json()
    assert data["brief"]["upstream_state"] == "sent"
    assert data["brief"]["current_version"] == 1
    assert data["brief"]["assigned_to_id"] == str(other_user.id)
    assert data["transfer"]["to_user_id"] == str(other_user.id)


def test_accept_brief(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    auth_headers_downstream: dict[str, str],
    draft_brief: Brief,
    downstream,
    db_session: Session,
) -> None:
    """Downstream can accept a sent brief."""
    review_response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=submit-review",
        headers=auth_headers_creator,
        json={"version": 1},
    )
    _complete_review_as_passed(db_session, review_response.json()["review_id"])

    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={"assigned_to": str(downstream.id)},
    )

    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/transfer?action=accept",
        headers=auth_headers_downstream,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["upstream_state"] == "in_process"
    assert data["brief"]["downstream_state"] == "opened"


def test_list_versions(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Versions endpoint lists all versions."""
    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=patch",
        headers=auth_headers_creator,
        json={"title": "Updated"},
    )

    response = client.get(
        f"/api/v1/briefs/{draft_brief.brief_id}/versions",
        headers=auth_headers_creator,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_specific_version(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Specific version content is returned via the detail endpoint."""
    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=patch",
        headers=auth_headers_creator,
        json={"title": "Updated"},
    )

    response = client.get(
        f"/api/v1/briefs/{draft_brief.brief_id}?version=1",
        headers=auth_headers_creator,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["is_current"] is False


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
    assert "owner_id" in data


def test_patch_brief_rejects_unknown_version(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Patching a non-existent version returns an error."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=patch",
        headers=auth_headers_creator,
        json={"version": 99, "title": "Updated Title"},
    )

    assert response.status_code == 404


def test_review_brief_rejects_stale_version(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Submitting a non-draft version for review returns an error."""
    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=submit-review",
        headers=auth_headers_creator,
        json={"version": 1},
    )

    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=submit-review",
        headers=auth_headers_creator,
        json={"version": 1},
    )

    assert response.status_code == 409
