import pytest
from unittest.mock import patch

@pytest.fixture
def app():
    with patch("modules.api.users.create_db.init_users_db"):
        from modules.api.main import create_app
        return create_app()

@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client

def test_create_app_returns_fastapi(app):
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)

def test_cors_middleware_configured(app):
    middlewares = [m.cls for m in app.user_middleware]
    from fastapi.middleware.cors import CORSMiddleware
    assert CORSMiddleware in middlewares

def test_routes_exist(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {}).keys()
    assert any(p.startswith("/auth") for p in paths)
    assert any(p.startswith("/users") for p in paths)
