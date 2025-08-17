from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from modules.api.auth.functions import (
    create_token,
    authenticate_user,
    store_refresh_token,
    find_refresh_token,
    verify_token,
)
from modules.api.auth.models import RefreshToken

# -------------------------------
# Setup global fake DB
# -------------------------------
fake_db = MagicMock()


# -------------------------------
# create_token
# -------------------------------
@patch("modules.api.auth.functions.jwt.encode")
def test_create_token_with_access_type(mock_encode):
    mock_encode.return_value = "mocked.jwt.token"
    data = {"sub": "123", "role": "admin", "type": "access"}
    token = create_token(data)
    assert token == "mocked.jwt.token"
    mock_encode.assert_called_once()


# -------------------------------
# authenticate_user
# -------------------------------
@patch("modules.api.auth.functions.get_user_by_email")
@patch("modules.api.auth.functions.verify_password")
@patch("modules.api.auth.functions.anonymize")
def test_authenticate_user_success(mock_anonymize, mock_verify_password, mock_get_user):
    email = "test@example.com"
    password = "correct-password"

    mock_anonymize.return_value = email
    mock_verify_password.return_value = True
    mock_get_user.return_value = type(
        "User", (), {"name": "Test", "hashed_password": "hashed_pwd"}
    )()

    user = authenticate_user(fake_db, email, password)

    assert user is not False
    mock_anonymize.assert_called_once_with(email)
    mock_get_user.assert_called_once()
    mock_verify_password.assert_called_once()


@patch("modules.api.auth.functions.get_user_by_email")
@patch("modules.api.auth.functions.anonymize")
def test_authenticate_user_not_found(mock_anonymize, mock_get_user):
    email = "nonexistent@example.com"
    password = "any"

    mock_anonymize.return_value = email
    mock_get_user.return_value = None

    result = authenticate_user(fake_db, email, password)
    assert result is False


@patch("modules.api.auth.functions.get_user_by_email")
@patch("modules.api.auth.functions.verify_password")
@patch("modules.api.auth.functions.anonymize")
def test_authenticate_user_invalid_password(
    mock_anonymize, mock_verify_password, mock_get_user
):
    email = "test@example.com"
    password = "wrong-password"

    mock_anonymize.return_value = email
    mock_verify_password.return_value = False
    mock_get_user.return_value = type("User", (), {"hashed_password": "hashed_pwd"})()

    result = authenticate_user(fake_db, email, password)
    assert result is False


# -------------------------------
# store_refresh_token
# -------------------------------
def test_store_refresh_token():
    fake_token_value = "some-refresh-token"
    fake_user_id = 1
    fake_expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    fake_db = MagicMock()

    store_refresh_token(fake_db, fake_user_id, fake_token_value, fake_expires_at)

    args, _ = fake_db.add.call_args
    added_obj = args[0]
    assert isinstance(added_obj, RefreshToken)
    assert added_obj.user_id == fake_user_id
    assert added_obj.token == fake_token_value
    assert added_obj.revoked is False
    assert added_obj.expires_at == fake_expires_at

    fake_db.commit.assert_called_once()


# -------------------------------
# find_refresh_token
# -------------------------------
def test_find_refresh_token_found():
    fake_token_value = "existing-token"

    fake_token = RefreshToken(
        user_id=1,
        token=fake_token_value,
        revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = fake_token

    result = find_refresh_token(fake_db, fake_token_value)
    assert result.token == fake_token_value


def test_find_refresh_token_not_found():
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = None

    result = find_refresh_token(fake_db, "nonexistent-token")
    assert result is None


# -------------------------------
# verify_token
# -------------------------------
@patch("modules.api.auth.functions.hash_token")
def test_verify_token_match(mock_hash_token):
    mock_hash_token.return_value = "hashed123"
    assert verify_token("token123", "hashed123") is True


@patch("modules.api.auth.functions.hash_token")
def test_verify_token_mismatch(mock_hash_token):
    mock_hash_token.return_value = "not_matching_hash"
    assert verify_token("token123", "hashed456") is False
