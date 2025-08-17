import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import SecurityScopes
from jose import JWTError
from modules.api.users.functions import get_current_user, get_user_by_email

fake_email = "anonymized@email.com"
fake_token = "fake.jwt.token"
fake_db = MagicMock()
fake_user = MagicMock(email=fake_email)
fake_token_data = {
    "sub": fake_email,
    "exp": 1737057317,
    "role": "admin",
    "scopes": ["reader", "admin"],
}


def test_get_user_by_email_found():
    fake_db.query().filter().first.return_value = fake_user
    user = get_user_by_email(fake_email, fake_db)
    assert user == fake_user


def test_get_user_by_email_not_found():
    fake_db.query().filter().first.return_value = None
    user = get_user_by_email(fake_email, fake_db)
    assert user is None


@patch("modules.api.users.functions.jwt.decode")
@patch("modules.api.users.functions.get_user_by_email")
def test_get_current_user_success(mock_get_user, mock_decode):
    mock_decode.return_value = fake_token_data
    mock_get_user.return_value = fake_user

    scopes = SecurityScopes(scopes=["reader"])
    token_data = get_current_user(security_scopes=scopes, token=fake_token, db=fake_db)

    assert token_data.sub == fake_email
    assert "reader" in token_data.scopes


@patch("modules.api.users.functions.jwt.decode", side_effect=JWTError)
def test_get_current_user_invalid_token(mock_decode):
    scopes = SecurityScopes(scopes=["reader"])
    with pytest.raises(HTTPException) as exc:
        get_current_user(security_scopes=scopes, token=fake_token, db=fake_db)
    assert exc.value.status_code == 401


@patch("modules.api.users.functions.jwt.decode")
def test_get_current_user_invalid_payload(mock_decode):
    mock_decode.return_value = {"invalid": "payload"}

    scopes = SecurityScopes(scopes=["reader"])
    with pytest.raises(HTTPException) as exc:
        get_current_user(security_scopes=scopes, token=fake_token, db=fake_db)
    assert exc.value.status_code == 400


@patch("modules.api.users.functions.jwt.decode", return_value=fake_token_data)
@patch("modules.api.users.functions.get_user_by_email", return_value=None)
def test_get_current_user_user_not_found(mock_get_user, mock_decode):
    scopes = SecurityScopes(scopes=["reader"])
    with pytest.raises(HTTPException) as exc:
        get_current_user(security_scopes=scopes, token=fake_token, db=fake_db)
    assert exc.value.status_code == 401


@patch("modules.api.users.functions.jwt.decode")
@patch("modules.api.users.functions.get_user_by_email", return_value=fake_user)
def test_get_current_user_forbidden_scope(mock_get_user, mock_decode):
    mock_decode.return_value = {
        "sub": fake_email,
        "exp": 1737057317,
        "role": "admin",
        "scopes": ["reader"],
    }
    scopes = SecurityScopes(scopes=["admin"])
    with pytest.raises(HTTPException) as exc:
        get_current_user(security_scopes=scopes, token=fake_token, db=fake_db)
    assert exc.value.status_code == 403
