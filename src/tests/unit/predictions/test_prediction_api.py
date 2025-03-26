"""
Tests for the prediction API endpoints.
"""
import pytest
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from src.predictions.interfaces import (
    PredictionResult,
    RecommendedAction,
    ActionSeverity
)
from src.predictions.api import create_prediction_router
from src.predictions.maintenance.component_failure import ComponentFailurePrediction


@pytest.fixture
def mock_prediction_service():
    """Mock prediction service for testing."""
    service = MagicMock()
    
    # Set up the mock to return a realistic prediction result
    async def mock_generate(*args, **kwargs):
        return PredictionResult(
            prediction_type="component_failure",
            device_id="test-device-123",
            predicted_value=0.75,
            confidence=0.85,
            features_used=["temperature", "pressure", "energy_usage"],
            timestamp=datetime.now(),
            recommended_actions=[
                RecommendedAction(
                    action_id="test-action-1",
                    description="Inspect heating element for signs of failure",
                    severity=ActionSeverity.HIGH,
                    impact="Water heater may fail to heat water properly",
                    expected_benefit="Prevent unexpected downtime and costly emergency repairs"
                )
            ],
            raw_details={
                "components": {
                    "heating_element": 0.85,
                    "thermostat": 0.35,
                    "pressure_valve": 0.65
                }
            }
        )
    
    service.generate_prediction = AsyncMock(side_effect=mock_generate)
    return service


@pytest.fixture
def app(mock_prediction_service):
    """Create a test FastAPI application."""
    app = FastAPI()
    prediction_router = create_prediction_router(mock_prediction_service)
    app.include_router(prediction_router, prefix="/api/predictions")
    return app


@pytest.fixture
def test_client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestPredictionAPI:
    """Test suite for the prediction API."""
    
    def test_list_prediction_types(self, test_client, mock_prediction_service):
        """Test listing available prediction types."""
        # Setup mock to return a list of prediction types
        mock_prediction_service.model_registry.list_models.return_value = {
            "component_failure": ["1.0.0", "1.1.0"],
            "descaling_requirement": ["1.0.0"],
            "lifespan_estimation": ["1.0.0"]
        }
        
        # Make request
        response = test_client.get("/api/predictions/types")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "prediction_types" in data
        assert "component_failure" in data["prediction_types"]
    
    def test_generate_prediction(self, test_client, mock_prediction_service):
        """Test generating a prediction."""
        # Prepare test data
        request_data = {
            "device_id": "test-device-123",
            "prediction_type": "component_failure",
            "features": {
                "temperature": [65.0, 68.0, 70.0],
                "pressure": [2.5, 2.6, 2.4],
                "energy_usage": [1200, 1250, 1300],
                "flow_rate": [9.5, 9.3, 9.1],
                "heating_cycles": [15, 16, 17],
                "total_operation_hours": 8760,
                "maintenance_history": [
                    {"type": "regular", "date": "2024-09-27T15:00:00Z"}
                ]
            }
        }
        
        # Make request
        response = test_client.post("/api/predictions/generate", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["prediction_type"] == "component_failure"
        assert data["device_id"] == "test-device-123"
        assert "predicted_value" in data
        assert "confidence" in data
        assert "recommended_actions" in data
        assert len(data["recommended_actions"]) > 0
        
        # Verify service was called correctly
        mock_prediction_service.generate_prediction.assert_called_once()
        call_args = mock_prediction_service.generate_prediction.call_args[1]
        assert call_args["prediction_type"] == "component_failure"
        assert call_args["device_id"] == "test-device-123"
    
    def test_generate_prediction_invalid_type(self, test_client, mock_prediction_service):
        """Test generating a prediction with invalid prediction type."""
        # Setup mock to raise ValueError for invalid prediction type
        mock_prediction_service.generate_prediction.side_effect = ValueError("Invalid prediction type")
        
        # Prepare test data
        request_data = {
            "device_id": "test-device-123",
            "prediction_type": "invalid_type",
            "features": {
                "temperature": [65.0, 68.0, 70.0]
            }
        }
        
        # Make request
        response = test_client.post("/api/predictions/generate", json=request_data)
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid prediction type" in data["detail"]
    
    def test_get_model_health(self, test_client, mock_prediction_service):
        """Test getting model health status."""
        # Setup mock to return health status
        mock_prediction_service.check_model_health.return_value = {
            "model_id": "component_failure-1.0.0-20250325152030",
            "prediction_type": "component_failure",
            "version": "1.0.0",
            "health_status": "healthy",
            "metrics": {
                "accuracy": 0.92,
                "precision": 0.88
            },
            "drift": {
                "feature_drift": {
                    "temperature": 0.05,
                    "pressure": 0.12
                },
                "overall_drift_score": 0.07
            },
            "recommendations": []
        }
        
        # Make request
        response = test_client.get("/api/predictions/health/component_failure-1.0.0-20250325152030")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["health_status"] == "healthy"
        assert "metrics" in data
        assert "drift" in data
    
    def test_get_device_predictions(self, test_client, mock_prediction_service):
        """Test getting predictions for a specific device."""
        # Setup mock to return predictions
        mock_prediction_service.get_device_predictions.return_value = [
            {
                "prediction_id": "pred-123",
                "prediction_type": "component_failure",
                "timestamp": datetime.now().isoformat(),
                "predicted_value": 0.75,
                "recommended_actions": [
                    {
                        "action_id": "action-123",
                        "description": "Inspect heating element",
                        "severity": "high"
                    }
                ]
            }
        ]
        
        # Make request
        response = test_client.get("/api/predictions/device/test-device-123")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) > 0
        assert data["predictions"][0]["prediction_type"] == "component_failure"
