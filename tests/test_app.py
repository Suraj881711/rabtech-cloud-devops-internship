"""Tests for the Flask app using the built-in test client.

These tests deliberately do not require PostgreSQL: the / and /health
endpoints never touch the database, and /items falls back gracefully.
"""

import pytest

from app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_payload(client):
    response = client.get("/")
    data = response.get_json()
    assert data["service"] == "rabtech-cloud-devops-internship"
    assert "message" in data


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_items_fallback(client):
    response = client.get("/items")
    assert response.status_code == 200
    items = response.get_json()["items"]
    assert isinstance(items, list)
    assert len(items) >= 1
