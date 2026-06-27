"""Tests for invite link endpoints and temporary user auth flows."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from briefchain.api.security import get_password_hash
from briefchain.models import Brief, BriefChain, BriefVersion, User
from briefchain.models.enums import (
    BriefPriority,
    BriefUpstreamState,
    BriefVersionStatus,
    UserType,
)

pytestmark = pytest.mark.usefixtures("jwt_secret")


@pytest.fixture
def reviewed_brief_for_invite(
    db_session: Session,
    creator: User,
) -> Brief:
    """Create a reviewed brief owned by creator."""
    brief = Brief(
        brief_id=UUID("11111111-1111-1111-1111-111111111111"),
        root_id=UUID("11111111-1111-1111-1111-111111111111"),
        parent_id=None,
        is_root=True,
        upstream_state=BriefUpstreamState.EDITING,
        downstream_state=None,
        current_version=None,
        title="Reviewed Brief",
        priority=BriefPriority.P2,
        created_by=creator.id,
        created_by_name=creator.name,
        assigned_to=None,
        assigned_to_name=None,
        status_changed_by=creator.id,
        status_changed_by_name=creator.name,
    )
    version = BriefVersion(
        brief_id=brief.brief_id,
        version=1,
        status=BriefVersionStatus.REVIEWED,
        title="Reviewed Brief",
        content="Content",
        attachments=[],
        priority=BriefPriority.P2,
        estimated_man_days=3.0,
        expected_completion_at=None,
        arbiter_review_id=None,
        is_upstream_changed=False,
        revision_reason="initial",
        modified_by=creator.id,
        modified_by_name=creator.name,
        change_summary="Initial version",
    )
    chain = BriefChain(
        chain_id=brief.brief_id,
        title="Reviewed Brief",
        owner_id=creator.id,
        owner_name=creator.name,
        priority=BriefPriority.P2,
    )
    db_session.add_all([brief, version, chain])
    db_session.commit()
    return brief


@pytest.fixture
def invite_response(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    reviewed_brief_for_invite: Brief,
):
    """Send a brief to an external recipient and return the response."""
    response = client.post(
        f"/api/v1/briefs/{reviewed_brief_for_invite.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_email": "external@example.com",
            "recipient_name": "External User",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_send_brief_to_external_creates_invite(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    reviewed_brief_for_invite: Brief,
) -> None:
    """Sending to an external email creates a temporary user and invite URL."""
    response = client.post(
        f"/api/v1/briefs/{reviewed_brief_for_invite.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_email": "external@example.com",
            "recipient_name": "External User",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["upstream_state"] == "sent"
    assert "invite" in data
    assert data["invite"]["invite_url"].startswith("/invites/")
    assert "accept_deadline" in data["invite"]
    assert "complete_deadline" in data["invite"]


def test_send_brief_to_anonymous_creates_invite(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    reviewed_brief_for_invite: Brief,
) -> None:
    """Sending without email/phone creates an anonymous temporary user and invite URL."""
    response = client.post(
        f"/api/v1/briefs/{reviewed_brief_for_invite.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_name": "Anonymous User",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["upstream_state"] == "sent"
    assert data["invite"]["invite_url"].startswith("/invites/")


def test_send_brief_to_existing_registered_email_uses_registered_user(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    reviewed_brief_for_invite: Brief,
    downstream: User,
) -> None:
    """Sending to an email of a registered user falls back to registered send."""
    response = client.post(
        f"/api/v1/briefs/{reviewed_brief_for_invite.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_email": downstream.email,
            "recipient_name": "Downstream",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["assigned_to_id"] == str(downstream.id)
    assert data.get("invite") is None


def test_send_brief_reuses_active_temporary_user(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    reviewed_brief_for_invite: Brief,
    db_session: Session,
) -> None:
    """Sending to an email of an active temporary user reuses the user_id."""
    # First send creates the temporary user
    first = client.post(
        f"/api/v1/briefs/{reviewed_brief_for_invite.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_email": "reuse@example.com",
            "recipient_name": "Reuse User",
        },
    )
    first_data = first.json()
    first_assigned_to = first_data["brief"]["assigned_to_id"]

    # Create a second reviewed brief
    brief2 = Brief(
        brief_id=UUID("22222222-2222-2222-2222-222222222222"),
        root_id=UUID("22222222-2222-2222-2222-222222222222"),
        parent_id=None,
        is_root=True,
        upstream_state=BriefUpstreamState.EDITING,
        downstream_state=None,
        current_version=None,
        title="Second Brief",
        priority=BriefPriority.P2,
        created_by=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        created_by_name="Creator",
        assigned_to=None,
        assigned_to_name=None,
        status_changed_by=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        status_changed_by_name="Creator",
    )
    version2 = BriefVersion(
        brief_id=brief2.brief_id,
        version=1,
        status=BriefVersionStatus.REVIEWED,
        title="Second Brief",
        content="Content",
        attachments=[],
        priority=BriefPriority.P2,
        estimated_man_days=3.0,
        expected_completion_at=None,
        arbiter_review_id=None,
        is_upstream_changed=False,
        revision_reason="initial",
        modified_by=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        modified_by_name="Creator",
        change_summary="Initial version",
    )
    chain2 = BriefChain(
        chain_id=brief2.brief_id,
        title="Second Brief",
        owner_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        owner_name="Creator",
        priority=BriefPriority.P2,
    )
    db_session.add_all([brief2, version2, chain2])
    db_session.commit()

    second = client.post(
        f"/api/v1/briefs/{brief2.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_email": "reuse@example.com",
            "recipient_name": "Reuse User",
        },
    )
    second_data = second.json()
    assert second_data["brief"]["assigned_to_id"] == first_assigned_to
    assert second_data["invite"]["invite_url"].startswith("/invites/")


def test_send_brief_to_finalized_temporary_user_uses_final_user(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    reviewed_brief_for_invite: Brief,
    db_session: Session,
) -> None:
    """Sending to an email of a temporary user with final_user_id falls back to that final user."""
    from briefchain.models import BriefInvite

    registered_user = User(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        email="final@example.com",
        name="Final User",
        user_type=UserType.REGISTERED,
        password_hash=get_password_hash("password123"),
    )
    temporary_user = User(
        id=UUID("44444444-4444-4444-4444-444444444444"),
        email="temp-final@example.com",
        name="Temp Final",
        user_type=UserType.TEMPORARY,
    )
    db_session.add_all([registered_user, temporary_user])
    db_session.commit()

    # Simulate an existing finalized invite
    invite = BriefInvite(
        id=UUID("55555555-5555-5555-5555-555555555555"),
        brief_id=reviewed_brief_for_invite.brief_id,
        nonce="oldnonce123",
        token="oldtoken",
        name="Old Invite",
        temporary_user_id=temporary_user.id,
        from_user=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        final_user_id=registered_user.id,
        accept_deadline=reviewed_brief_for_invite.created_at,
        complete_deadline=reviewed_brief_for_invite.created_at,
        invalidated_at=reviewed_brief_for_invite.created_at,
    )
    db_session.add(invite)
    db_session.commit()

    response = client.post(
        f"/api/v1/briefs/{reviewed_brief_for_invite.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_email": "temp-final@example.com",
            "recipient_name": "Temp Final",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["assigned_to_id"] == str(registered_user.id)
    assert data.get("invite") is None


def test_view_invite(
    client: TestClient,
    invite_response: dict,
) -> None:
    """GET /invites/{token} returns invite and brief details."""
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    response = client.get(f"/api/v1/invites/{token}")

    assert response.status_code == 200
    data = response.json()
    assert data["invite"]["name"] == "External User"
    assert data["brief"]["upstream_state"] == "sent"


def test_view_invite_rejects_tampered_token(
    client: TestClient,
    invite_response: dict,
) -> None:
    """A tampered invite token is rejected."""
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]
    tampered = token[:-1] + ("0" if token[-1] != "0" else "1")

    response = client.get(f"/api/v1/invites/{tampered}")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVITE_INVALID_TOKEN"


def test_accept_invite(
    client: TestClient,
    invite_response: dict,
) -> None:
    """POST /invites/{token}/transfer?action=accept accepts the brief."""
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    response = client.post(f"/api/v1/invites/{token}/transfer?action=accept")

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["upstream_state"] == "in_process"
    assert data["brief"]["downstream_state"] == "opened"


def test_reject_invite(
    client: TestClient,
    invite_response: dict,
) -> None:
    """POST /invites/{token}/transfer?action=reject rejects the brief."""
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    response = client.post(
        f"/api/v1/invites/{token}/transfer?action=reject",
        json={"reason": "Unclear requirements"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["upstream_state"] == "editing"


def test_reject_invite_requires_reason(
    client: TestClient,
    invite_response: dict,
) -> None:
    """Rejecting without a reason returns 422."""
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    response = client.post(f"/api/v1/invites/{token}/transfer?action=reject", json={})

    assert response.status_code == 422


def test_register_with_invite_token_upgrades_temporary_user(
    client: TestClient,
    invite_response: dict,
    db_session: Session,
) -> None:
    """Registering with invite_token upgrades the temporary user in place."""
    brief_id = invite_response["brief"]["brief_id"]
    brief = db_session.get(Brief, UUID(brief_id))
    temporary_user_id = str(brief.assigned_to)
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "external@example.com",
            "password": "password123",
            "name": "Registered External",
            "temporary_user_id": temporary_user_id,
            "invite_token": token,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["upgraded_from_temporary"] is True
    assert data["user"]["user_type"] == "registered"

    # Verify brief assigned_to is unchanged (same UUID, now registered)
    brief = db_session.get(Brief, UUID(brief_id))
    assert brief.assigned_to == UUID(data["user"]["id"])


def test_register_migrates_all_active_briefs(
    client: TestClient,
    auth_headers_creator: dict[str, str],
    reviewed_brief_for_invite: Brief,
    db_session: Session,
) -> None:
    """Registering with invite_token migrates all active briefs of the temporary user."""
    # Send first brief
    first_response = client.post(
        f"/api/v1/briefs/{reviewed_brief_for_invite.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_email": "multi@example.com",
            "recipient_name": "Multi Brief User",
        },
    )
    first_data = first_response.json()
    first_brief = db_session.get(Brief, reviewed_brief_for_invite.brief_id)
    temporary_user_id = str(first_brief.assigned_to)
    invite_url = first_data["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    # Create and send second brief to the same temporary user
    brief2 = Brief(
        brief_id=UUID("66666666-6666-6666-6666-666666666666"),
        root_id=UUID("66666666-6666-6666-6666-666666666666"),
        parent_id=None,
        is_root=True,
        upstream_state=BriefUpstreamState.EDITING,
        downstream_state=None,
        current_version=None,
        title="Second Brief",
        priority=BriefPriority.P2,
        created_by=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        created_by_name="Creator",
        assigned_to=None,
        assigned_to_name=None,
        status_changed_by=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        status_changed_by_name="Creator",
    )
    version2 = BriefVersion(
        brief_id=brief2.brief_id,
        version=1,
        status=BriefVersionStatus.REVIEWED,
        title="Second Brief",
        content="Content",
        attachments=[],
        priority=BriefPriority.P2,
        estimated_man_days=3.0,
        expected_completion_at=None,
        arbiter_review_id=None,
        is_upstream_changed=False,
        revision_reason="initial",
        modified_by=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        modified_by_name="Creator",
        change_summary="Initial version",
    )
    chain2 = BriefChain(
        chain_id=brief2.brief_id,
        title="Second Brief",
        owner_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        owner_name="Creator",
        priority=BriefPriority.P2,
    )
    db_session.add_all([brief2, version2, chain2])
    db_session.commit()

    client.post(
        f"/api/v1/briefs/{brief2.brief_id}/transfer?action=send",
        headers=auth_headers_creator,
        json={
            "is_temporary_user": True,
            "recipient_email": "multi@example.com",
            "recipient_name": "Multi Brief User",
        },
    )

    # Register with invite_token
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "multi@example.com",
            "password": "password123",
            "name": "Registered Multi",
            "temporary_user_id": temporary_user_id,
            "invite_token": token,
        },
    )

    assert response.status_code == 201
    registered_id = response.json()["user"]["id"]

    brief1 = db_session.get(Brief, reviewed_brief_for_invite.brief_id)
    brief2_loaded = db_session.get(Brief, brief2.brief_id)
    assert brief1.assigned_to == UUID(registered_id)
    assert brief2_loaded.assigned_to == UUID(registered_id)


def test_login_with_invite_token_links_brief(
    client: TestClient,
    invite_response: dict,
    db_session: Session,
) -> None:
    """Logging in with invite_token migrates brief ownership to the registered user."""
    brief_id = invite_response["brief"]["brief_id"]
    brief = db_session.get(Brief, UUID(brief_id))
    temporary_user_id = str(brief.assigned_to)
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    # Create a registered user with a different email
    registered_user = User(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        email="registered@example.com",
        name="Registered External",
        user_type=UserType.REGISTERED,
        password_hash=get_password_hash("password123"),
    )
    db_session.add(registered_user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "registered@example.com",
            "password": "password123",
            "temporary_user_id": temporary_user_id,
            "invite_token": token,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["linked_temporary_user"] is not None
    assert data["user"]["id"] == str(registered_user.id)

    brief = db_session.get(Brief, UUID(brief_id))
    assert brief.assigned_to == registered_user.id


def test_temporary_user_cannot_login_with_password(
    client: TestClient,
    invite_response: dict,
) -> None:
    """A temporary user cannot log in with a password."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "external@example.com",
            "password": "anypassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TEMPORARY_USER_CANNOT_LOGIN"


def test_invite_invalidated_after_register(
    client: TestClient,
    invite_response: dict,
    db_session: Session,
) -> None:
    """Invite token is invalidated after temporary user registers."""
    brief_id = invite_response["brief"]["brief_id"]
    brief = db_session.get(Brief, UUID(brief_id))
    temporary_user_id = str(brief.assigned_to)
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "external@example.com",
            "password": "password123",
            "name": "Registered External",
            "temporary_user_id": temporary_user_id,
            "invite_token": token,
        },
    )

    response = client.get(f"/api/v1/invites/{token}")
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "INVITE_INVALIDATED"


def test_block_invite(
    client: TestClient,
    invite_response: dict,
) -> None:
    """POST /invites/{token}/downstream-actions?action=block marks brief
    downstream_state as blocked."""
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    # First accept the brief
    client.post(f"/api/v1/invites/{token}/transfer?action=accept")

    response = client.post(
        f"/api/v1/invites/{token}/downstream-actions?action=block",
        json={"content": "Need clarification"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["downstream_state"] == "blocked"


def test_submit_invite(
    client: TestClient,
    invite_response: dict,
) -> None:
    """POST /invites/{token}/downstream-actions?action=submit marks brief
    downstream_state as submitted."""
    invite_url = invite_response["invite"]["invite_url"]
    token = invite_url.split("/invites/")[1]

    # First accept the brief
    client.post(f"/api/v1/invites/{token}/transfer?action=accept")

    response = client.post(
        f"/api/v1/invites/{token}/downstream-actions?action=submit",
        json={"content": "Completed all tasks"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["downstream_state"] == "submitted"
