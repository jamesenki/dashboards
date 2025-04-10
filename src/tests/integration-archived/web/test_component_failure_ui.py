"""
Integration tests for the Component Failure Prediction UI.
"""
import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.predictions.interfaces import PredictionResult
from src.web.simple_app import create_app


@pytest.fixture
def app() -> FastAPI:
    """Create test application."""
    return create_app(testing=True)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_ui_no_external_resources(client):
    """Test that the UI doesn't depend on external resources."""
    response = client.get("/")
    assert response.status_code == 200

    html_content = response.text

    # Verify no external resources are loaded
    assert "cdn.jsdelivr.net" not in html_content
    assert "cdnjs.cloudflare.com" not in html_content
    assert "https://" not in html_content
    assert "http://" not in html_content

    # Check no font-awesome icon references
    assert "fas " not in html_content
    assert "far " not in html_content
    assert "fa-" not in html_content


def test_ui_renders_with_predictions(client, monkeypatch):
    """Test that the UI renders with prediction data."""
    # Check that prediction data is displayed when available
    response = client.get("/?has_predictions=true")
    assert response.status_code == 200

    html_content = response.text

    # Verify prediction components are displayed
    assert "Component Health" in html_content
    assert "Recommended Actions" in html_content
    assert "component-health-details" in html_content


def test_ui_error_handling(client):
    """Test that the UI handles errors gracefully."""
    # Force an error
    response = client.get("/?force_error=true")
    assert response.status_code == 500

    html_content = response.text

    # Verify error message is displayed
    assert "Error" in html_content
    assert "An error occurred" in html_content
