"""HTTP API tests for OpenGov Food."""

from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from opengovfood.core.config import get_settings
from opengovfood.web.app import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert payload["status"] == "healthy"


def test_root_endpoint():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert payload["name"] == "OpenGov Food"


def test_openapi_schema():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        assert "paths" in response.json()


def test_user_registration_and_login():
    with TestClient(app) as client:
        registration_data = {
            "email": "tester@example.com",
            "password": "StrongPass123",
            "full_name": "QA Tester",
        }
        register_response = client.post("/api/v1/users/open", json=registration_data)
        assert register_response.status_code == status.HTTP_200_OK

        login_payload = {
            "username": registration_data["email"],
            "password": registration_data["password"],
        }
        login_response = client.post(
            "/api/v1/users/login/access-token",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        assert token


def test_protected_route_requires_auth():
    with TestClient(app) as client:
        response = client.get("/api/v1/items")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authenticated_item_crud():
    with TestClient(app) as client:
        settings = get_settings()

        login_response = client.post(
            "/api/v1/users/login/access-token",
            data={
                "username": settings.FIRST_SUPERUSER,
                "password": settings.FIRST_SUPERUSER_PASSWORD,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        login_response.raise_for_status()
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        item_payload = {"title": "Inspection A", "description": "Routine inspection"}
        create_response = client.post("/api/v1/items", json=item_payload, headers=headers)
        assert create_response.status_code == status.HTTP_200_OK
        item_id = create_response.json()["id"]

        read_response = client.get(f"/api/v1/items/{item_id}", headers=headers)
        assert read_response.status_code == status.HTTP_200_OK

        update_response = client.put(
            f"/api/v1/items/{item_id}",
            json={"title": "Inspection B"},
            headers=headers,
        )
        assert update_response.status_code == status.HTTP_200_OK

        list_response = client.get("/api/v1/items", headers=headers)
        assert list_response.status_code == status.HTTP_200_OK

        delete_response = client.delete(f"/api/v1/items/{item_id}", headers=headers)
        assert delete_response.status_code == status.HTTP_200_OK


# Additional pytest configuration
pytest_plugins = ["pytest_asyncio"]

# Test markers for organization
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]

# Coverage configuration for API tests
def pytest_configure(config):
    """Configure pytest for API tests."""
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )