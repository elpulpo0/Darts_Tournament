import pytest
from unittest.mock import patch, MagicMock, mock_open
import yaml

import modules.api.users.models as users_models
import modules.api.users.create_db as create_db


@pytest.fixture(autouse=True)
def patch_logger():
    with patch("modules.api.users.create_db.logger") as mock_logger:
        yield mock_logger


@pytest.fixture
def fake_config():
    return {
        "roles": ["admin", "user"],
        "users": [
            {
                "email": "admin@example.com",
                "trigram": "AUS",
                "name": "Admin User",
                "password": "adminpass",
                "role": "admin",
            },
            {
                "email": "user@example.com",
                "trigram": "NUS",
                "name": "Normal User",
                "password": "userpass",
                "role": "user",
            },
        ],
    }


def test_load_initial_users_config_file_not_found():
    mock_path = MagicMock()
    mock_path.exists.return_value = False

    with patch("modules.api.users.create_db.INITIAL_USERS_CONFIG_PATH", mock_path):
        with pytest.raises(FileNotFoundError):
            create_db.load_initial_users_config()


def test_load_initial_users_config_file_exists(fake_config):
    mock_path = MagicMock()
    mock_path.exists.return_value = True

    m = mock_open(read_data=yaml.dump(fake_config))

    with patch("modules.api.users.create_db.INITIAL_USERS_CONFIG_PATH", mock_path):
        with patch("builtins.open", m):
            config = create_db.load_initial_users_config()
            assert config == fake_config


@patch("modules.api.users.create_db.UsersBase.metadata.create_all")
def test_init_users_db_creates_db_when_not_exists(mock_create_all, patch_logger):
    mock_db_path = MagicMock()
    mock_db_path.exists.return_value = False

    with patch("modules.api.users.create_db.USERS_DATABASE_PATH", mock_db_path):
        with patch(
            "modules.api.users.create_db.create_roles_and_first_users"
        ) as mock_create_users:
            create_db.init_users_db()
            mock_create_all.assert_called_once_with(bind=create_db.users_engine)
            mock_create_users.assert_called_once()
            patch_logger.info.assert_any_call(
                "The 'users' database does not exist. Creating it..."
            )
            patch_logger.info.assert_any_call(
                "The 'users' database was successfully created."
            )


def test_init_users_db_does_nothing_if_db_exists(patch_logger):
    mock_db_path = MagicMock()
    mock_db_path.exists.return_value = True

    with patch("modules.api.users.create_db.USERS_DATABASE_PATH", mock_db_path):
        with patch(
            "modules.api.users.create_db.create_roles_and_first_users"
        ) as mock_create_users:
            create_db.init_users_db()
            mock_create_users.assert_not_called()
            patch_logger.info.assert_called_with(
                "The 'users' database already exists. No changes needed."
            )


@patch("modules.api.users.create_db.load_initial_users_config")
@patch("modules.api.users.create_db.UsersSessionLocal")
@patch("modules.api.users.create_db.anonymize", side_effect=lambda x: f"anon-{x}")
@patch("modules.api.users.create_db.hash_password", side_effect=lambda x: f"hashed-{x}")
def test_create_roles_and_first_users_success(
    mock_hash_password, mock_anonymize, mock_users_session_local, mock_load_config
):
    fake_config = {
        "roles": ["admin", "user"],
        "users": [
            {
                "email": "admin@example.com",
                "trigram": "AUS",
                "name": "Admin User",
                "password": "adminpass",
                "role": "admin",
            },
            {
                "email": "user@example.com",
                "trigram": "NUS",
                "name": "Normal User",
                "password": "userpass",
                "role": "user",
            },
        ],
    }
    mock_load_config.return_value = fake_config

    mock_db = MagicMock()
    mock_users_session_local.return_value = mock_db

    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    mock_db.query.return_value.all.return_value = [
        users_models.Role(role="admin", id=1),
        users_models.Role(role="user", id=2),
    ]

    create_db.create_roles_and_first_users()

    added_roles = [
        call.args[0]
        for call in mock_db.add.call_args_list
        if isinstance(call.args[0], users_models.Role)
    ]
    added_users = [
        call.args[0]
        for call in mock_db.add.call_args_list
        if isinstance(call.args[0], users_models.User)
    ]

    assert set(r.role for r in added_roles) == set(fake_config["roles"])
    assert len(added_users) == len(fake_config["users"])


@patch("modules.api.users.create_db.load_initial_users_config")
@patch("modules.api.users.create_db.UsersSessionLocal")
def test_create_roles_and_first_users_role_missing_raises(
    mock_users_session_local, mock_load_config
):
    bad_config = {
        "roles": ["admin"],
        "users": [
            {
                "email": "someone@example.com",
                "trigram": "SUS",
                "name": "Some User",
                "password": "pass",
                "role": "user",
            },
        ],
    }
    mock_load_config.return_value = bad_config
    mock_db = MagicMock()
    mock_users_session_local.return_value = mock_db

    def filter_by_side_effect(role=None, **kwargs):
        if role == "admin":
            return MagicMock(first=lambda: users_models.Role(role="admin", id=1))
        return MagicMock(first=lambda: None)

    mock_db.query.return_value.filter_by.side_effect = filter_by_side_effect
    mock_db.query.return_value.all.return_value = [
        users_models.Role(role="admin", id=1)
    ]

    with pytest.raises(ValueError, match="The role 'user' does not exist"):
        create_db.create_roles_and_first_users()


@patch("modules.api.users.create_db.load_initial_users_config")
@patch("modules.api.users.create_db.UsersSessionLocal")
@patch("modules.api.users.create_db.logger")
def test_create_roles_and_first_users_raises_exception_when_query_fails(
    mock_logger, mock_users_session_local, mock_load_config
):
    fake_config = {"roles": ["admin", "user"], "users": []}

    mock_load_config.return_value = fake_config
    mock_db = MagicMock()
    mock_users_session_local.return_value = mock_db

    mock_db.query.return_value.filter_by.side_effect = Exception("DB error")

    with pytest.raises(Exception, match="DB error"):
        create_db.create_roles_and_first_users()

    mock_db.rollback.assert_called_once()
    mock_logger.error.assert_called_once()
