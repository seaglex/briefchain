"""Unit tests for invite token generation and validation."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from briefchain.api.config import settings
from briefchain.api.exceptions import APIError
from briefchain.api.services import invites as invite_service

pytestmark = pytest.mark.usefixtures("jwt_secret")


def test_generate_and_verify_invite_token() -> None:
    """A generated token can be parsed and verified."""
    brief_id = uuid4()
    temporary_user_id = uuid4()
    nonce = "testnonce123"
    deadline = datetime.now(UTC) + timedelta(days=7)

    token = invite_service.generate_invite_token(brief_id, temporary_user_id, nonce, deadline)
    parsed = invite_service.verify_invite_token_signature(token)
    parsed_brief_id, parsed_temporary_user_id, parsed_nonce, parsed_epoch = parsed

    assert parsed_brief_id == brief_id
    assert parsed_temporary_user_id == temporary_user_id
    assert parsed_nonce == nonce
    assert parsed_epoch == int(deadline.timestamp())


def test_tampered_token_rejected() -> None:
    """A token with an invalid signature is rejected."""
    brief_id = uuid4()
    temporary_user_id = uuid4()
    nonce = "testnonce123"
    deadline = datetime.now(UTC) + timedelta(days=7)

    token = invite_service.generate_invite_token(brief_id, temporary_user_id, nonce, deadline)
    tampered = token[:-1] + ("0" if token[-1] != "0" else "1")

    with pytest.raises(APIError) as exc_info:
        invite_service.verify_invite_token_signature(tampered)

    assert exc_info.value.code == "INVITE_INVALID_TOKEN"


def test_expired_token_rejected(db_session) -> None:
    """A token past its accept_deadline is rejected."""
    brief_id = uuid4()
    temporary_user_id = uuid4()
    nonce = "testnonce123"
    deadline = datetime.now(UTC) - timedelta(seconds=1)

    token = invite_service.generate_invite_token(brief_id, temporary_user_id, nonce, deadline)

    with pytest.raises(APIError) as exc_info:
        invite_service.get_invite_by_token(db_session, token)

    assert exc_info.value.code == "INVITE_EXPIRED"


def test_invalid_token_format_rejected() -> None:
    """A malformed token is rejected."""
    with pytest.raises(APIError) as exc_info:
        invite_service.parse_invite_token("not-a-valid-token")

    assert exc_info.value.code == "INVITE_INVALID_TOKEN"


def test_sign_payload_uses_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """The HMAC signature depends on the configured JWT secret."""
    brief_id = uuid4()
    temporary_user_id = uuid4()
    nonce = "testnonce123"
    deadline = datetime.now(UTC) + timedelta(days=7)

    token_a = invite_service.generate_invite_token(brief_id, temporary_user_id, nonce, deadline)
    assert invite_service.verify_invite_token_signature(token_a)

    monkeypatch.setattr(settings, "jwt_secret_key", "different-secret")
    token_b = invite_service.generate_invite_token(brief_id, temporary_user_id, nonce, deadline)
    assert token_a != token_b
    assert invite_service.verify_invite_token_signature(token_b)
    with pytest.raises(APIError):
        invite_service.verify_invite_token_signature(token_a)


def test_get_invite_by_token_accepts_url_encoded_token(db_session) -> None:
    """An accidentally URL-encoded token is decoded and accepted."""
    from briefchain.models import BriefInvite, User
    from briefchain.models.enums import UserType

    brief_id = uuid4()
    temporary_user = User(
        id=uuid4(),
        name="Temp",
        user_type=UserType.TEMPORARY,
    )
    nonce = "testnonce123"
    deadline = datetime.now(UTC) + timedelta(days=7)
    token = invite_service.generate_invite_token(brief_id, temporary_user.id, nonce, deadline)
    invite = BriefInvite(
        id=uuid4(),
        brief_id=brief_id,
        nonce=nonce,
        token=token,
        name="Test",
        temporary_user_id=temporary_user.id,
        from_user=uuid4(),
        accept_deadline=deadline,
        complete_deadline=deadline,
    )
    db_session.add_all([temporary_user, invite])
    db_session.commit()

    encoded_token = token.replace(":", "%3A")
    result = invite_service.get_invite_by_token(db_session, encoded_token)
    assert result.id == invite.id
