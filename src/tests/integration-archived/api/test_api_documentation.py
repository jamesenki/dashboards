"""
Integration tests for API documentation.

These tests verify that:
1. OpenAPI schema includes documentation for both database and mock API endpoints
2. Endpoints have clear descriptions of their purpose and parameters
3. API documentation is accessible through Swagger UI
"""
import pytest
from fastapi.testclient import TestClient

from src.main import app

# Create test client
client = TestClient(app)


class TestApiDocumentation:
    """Test suite for API documentation."""

    def test_openapi_schema_includes_water_heater_apis(self):
        """Test that the OpenAPI schema includes documentation for water heater APIs."""
        # Get the OpenAPI schema
        response = client.get("/api/openapi.json")
        assert response.status_code == 200

        # Parse the schema
        schema = response.json()

        # Check that the schema includes our API tags
        tags = [tag["name"] for tag in schema.get("tags", [])]
        assert "db" in tags
        assert "mock" in tags
        assert "water-heaters" in tags

        # Check that the schema includes our separate API endpoints
        paths = schema.get("paths", {})

        # Database API paths
        assert "/api/db/water-heaters/" in paths
        assert "/api/db/water-heaters/health" in paths
        assert "/api/db/water-heaters/data-source" in paths

        # Mock API paths
        assert "/api/mock/water-heaters/" in paths
        assert "/api/mock/water-heaters/simulate/failure" in paths
        assert "/api/mock/water-heaters/simulation/status" in paths
        assert "/api/mock/water-heaters/data-source" in paths

        # Check that endpoints have descriptions
        # Test one endpoint from each API for documentation
        db_endpoint = paths.get("/api/db/water-heaters/", {})
        mock_endpoint = paths.get("/api/mock/water-heaters/", {})

        for endpoint in [db_endpoint, mock_endpoint]:
            if "get" in endpoint:
                assert "description" in endpoint["get"]
                assert "summary" in endpoint["get"]
            if "post" in endpoint:
                assert "description" in endpoint["post"]
                assert "summary" in endpoint["post"]

    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_redoc_accessible(self):
        """Test that ReDoc is accessible."""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()
