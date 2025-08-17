import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.database.session import UsersBase
from modules.database.dependencies import get_users_db
from modules.api.users.models import User, Role
from modules.api.auth.security import hash_password, anonymize

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)


def test_routes_presence(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {}).keys()
    print("Available routes:", list(paths))
    assert "/auth/login" in paths
    assert "/users" in paths or any(p.startswith("/users") for p in paths)


@pytest.fixture(scope="function")
def db():
    UsersBase.metadata.drop_all(bind=engine)
    UsersBase.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db):
    with patch("modules.api.main.init_users_db"):
        from modules.api.main import app

        def override_get_users_db():
            yield db

        app.dependency_overrides[get_users_db] = override_get_users_db

        with TestClient(app) as c:
            yield c

        app.dependency_overrides.clear()


@pytest.fixture
def create_roles(db):
    role_user = Role(role="user")
    role_admin = Role(role="admin")
    db.add_all([role_user, role_admin])
    db.commit()
    db.refresh(role_user)
    db.refresh(role_admin)
    return role_user, role_admin


@pytest.fixture
def create_test_user(db, create_roles):
    role_user, _ = create_roles
    user = User(
        email=anonymize("test@example.com"),
        trigram="TUS",
        name="Test User",
        hashed_password=hash_password("password123"),
        role_id=role_user.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def create_admin_user(db, create_roles):
    _, role_admin = create_roles
    admin = User(
        email=anonymize("admin@example.com"),
        name="Admin User",
        trigram="AUS",
        hashed_password=hash_password("adminpass"),
        role_id=role_admin.id,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def login(client, email, password):
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    return json_data["access_token"], json_data.get("refresh_token")


# -------- AUTH ROUTES --------


def test_login_success(client, create_test_user):
    access_token, refresh_token = login(client, "test@example.com", "password123")
    assert access_token
    assert refresh_token


def test_login_invalid_password(client, create_test_user):
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_refresh_token_success(client, create_test_user):
    _, refresh_token = login(client, "test@example.com", "password123")
    response = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_tokens_requires_admin(client, create_admin_user):
    access_token, _ = login(client, "admin@example.com", "adminpass")
    response = client.get(
        "/auth/refresh-tokens",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_refresh_tokens_forbidden_for_non_admin(client, create_test_user):
    access_token, _ = login(client, "test@example.com", "password123")
    response = client.get(
        "/auth/refresh-tokens",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403


# -------- USERS ROUTES --------


def test_get_current_user(client, create_test_user):
    access_token, _ = login(client, "test@example.com", "password123")
    response = client.get(
        "/users/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == anonymize("test@example.com")
    assert data["name"] == "Test User"


def test_user_cannot_list_all_users(client, create_test_user):
    access_token, _ = login(client, "test@example.com", "password123")
    response = client.get(
        "users/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403


def test_admin_can_list_all_users(client, create_admin_user, create_test_user):
    access_token, _ = login(client, "admin@example.com", "adminpass")
    response = client.get(
        "users/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    users = response.json()
    assert any(u["email"] == anonymize("test@example.com") for u in users)
    assert any(u["email"] == anonymize("admin@example.com") for u in users)


def test_get_user_by_id_admin(client, create_admin_user, create_test_user):
    access_token, _ = login(client, "admin@example.com", "adminpass")
    user_id = create_test_user.id
    response = client.get(
        f"/users/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id


def test_get_user_by_id_forbidden_for_non_admin(client, create_test_user):
    access_token, _ = login(client, "test@example.com", "password123")
    user_id = create_test_user.id
    response = client.get(
        f"/users/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403


def test_update_current_user(client, create_test_user):
    access_token, _ = login(client, "test@example.com", "password123")
    response = client.patch(
        "/users/users/me",
        json={"name": "New Name", "email": "newemail@example.com"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["email"] == anonymize("newemail@example.com")


def test_admin_can_update_any_user(client, create_admin_user, create_test_user):
    access_token, _ = login(client, "admin@example.com", "adminpass")
    user_id = create_test_user.id
    response = client.patch(
        f"/users/users/{user_id}",
        json={"name": "Admin Changed", "email": "adminchanged@example.com"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Admin Changed"
    assert data["email"] == anonymize("adminchanged@example.com")


def test_user_cannot_update_other_user(client, create_test_user, create_admin_user):
    access_token, _ = login(client, "test@example.com", "password123")
    user_id = create_admin_user.id
    response = client.patch(
        f"/users/users/{user_id}",
        json={"name": "Hack Name"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403


def test_admin_can_delete_user(client, create_admin_user, create_test_user):
    access_token, _ = login(client, "admin@example.com", "adminpass")
    user_id = create_test_user.id
    response = client.delete(
        f"/users/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


def test_user_cannot_delete_user(client, create_test_user):
    access_token, _ = login(client, "test@example.com", "password123")
    response = client.delete(
        f"/users/users/{create_test_user.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403


@pytest.fixture(scope="session", autouse=True)
def db_file_cleanup():
    if os.path.exists("test.db"):
        os.remove("test.db")

    yield

    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")
