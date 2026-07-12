"""Tests for Arbiter review API endpoints."""

from __future__ import annotations

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


def test_create_review_returns_202(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """POST /briefs/:id/reviews triggers an async review."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews",
        headers=auth_headers_creator,
        json={},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["brief_id"] == str(draft_brief.brief_id)
    assert data["brief_version"] == 1
    assert data["status"] == "processing"
    assert "review_id" in data


def test_create_review_rejects_duplicate(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """A second review request while one is processing returns 409."""
    client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews",
        headers=auth_headers_creator,
        json={},
    )
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews",
        headers=auth_headers_creator,
        json={},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REVIEW_ALREADY_IN_PROGRESS"


def test_create_review_rejects_non_creator(
    client: TestClient,
    auth_headers_downstream: dict[str, str],
    draft_brief: Brief,
) -> None:
    """Only the creator can trigger a review."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews",
        headers=auth_headers_downstream,
        json={},
    )

    assert response.status_code == 403


def test_get_review_processing(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """GET returns a processing review."""
    create_response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews",
        headers=auth_headers_creator,
        json={},
    )
    review_id = create_response.json()["review_id"]

    response = client.get(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews/{review_id}",
        headers=auth_headers_creator,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["review_id"] == review_id
    assert data["status"] == "processing"
    assert data["attempt_count"] == 0


def test_get_review_passed(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
    db_session: Session,
) -> None:
    """GET returns a passed review with score and suggestions."""
    create_response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews",
        headers=auth_headers_creator,
        json={},
    )
    review_id = create_response.json()["review_id"]
    _complete_review_as_passed(db_session, review_id)

    response = client.get(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews/{review_id}",
        headers=auth_headers_creator,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "passed"
    assert data["score"] == 80
    assert data["reviewed_at"] is not None


def test_get_review_not_found(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """GET returns 404 for an unknown review."""
    response = client.get(
        f"/api/v1/briefs/{draft_brief.brief_id}/reviews/{UUID(int=0)}",
        headers=auth_headers_creator,
    )

    assert response.status_code == 404


def test_submit_review_action_returns_202(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
) -> None:
    """The legacy submit-review action returns 202 and creates a review."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/editing?action=submit-review",
        headers=auth_headers_creator,
        json={"version": 1},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "processing"
    assert data["brief_version"] == 1


def test_send_requires_passed_review(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    draft_brief: Brief,
    downstream,
) -> None:
    """Send is rejected when the latest review has not passed."""
    response = client.post(
        f"/api/v1/briefs/{draft_brief.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={"assigned_to": str(downstream.id)},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REVIEW_REQUIRED"
