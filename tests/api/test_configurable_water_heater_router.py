"""
Tests for the configurable water heater API router.
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
import json
from unittest.mock import AsyncMock, patch

from src.api.water_heater.configurable_router import router
from src.services.configurable_water_heater_service import ConfigurableWaterHeaterService
from src.models.water_heater import WaterHeater, WaterHeaterMode, WaterHeaterStatus
from src.repositories.water_heater_repository import MockWaterHeaterRepository

app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)

@pytest.fixture
def mock_repository():
    return MockWaterHeaterRepository()

@pytest.fixture
def mock_service(mock_repository):
    service = ConfigurableWaterHeaterService(repository=mock_repository)
    return service

@pytest.fixture
def sample_water_heater():
    return WaterHeater(
        id="wh-test-123",
        name="Test Water Heater",
        model="EcoHeat 2000",
        manufacturer="WaterTech Inc.",
        current_temperature=45.5,
        target_temperature=50.0,
        status=WaterHeaterStatus.IDLE,
        mode=WaterHeaterMode.NORMAL,
        health_status="GREEN"
    )

@pytest.fixture
def sample_health_config():
    return {
        "temperature_high": {"threshold": 70.0, "status": "RED"},
        "temperature_warning": {"threshold": 65.0, "status": "YELLOW"},
        "pressure_high": {"threshold": 6.0, "status": "RED"}
    }

@pytest.fixture
def sample_alert_rule():
    return {
        "id": "rule1",
        "name": "High Temperature Alert",
        "condition": "temperature > 75",
        "severity": "HIGH",
        "message": "Water heater temperature exceeds safe level",
        "enabled": True
    }

class TestConfigurableWaterHeaterRouter:
    """Tests for the configurable water heater API router."""
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_get_water_heaters(self, mock_service_class, mock_service, sample_water_heater):
        """Test getting all water heaters."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.get_water_heaters = AsyncMock(return_value=[sample_water_heater])
        
        # Make request
        response = client.get("/api/v1/water-heaters")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_water_heater.id
        assert data[0]["name"] == sample_water_heater.name
        
        # Verify service was called
        mock_service.get_water_heaters.assert_called_once()
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_get_water_heater(self, mock_service_class, mock_service, sample_water_heater):
        """Test getting a specific water heater."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.get_water_heater = AsyncMock(return_value=sample_water_heater)
        
        # Make request
        response = client.get(f"/api/v1/water-heaters/{sample_water_heater.id}")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_water_heater.id
        assert data["name"] == sample_water_heater.name
        
        # Verify service was called
        mock_service.get_water_heater.assert_called_once_with(sample_water_heater.id)
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_get_water_heater_not_found(self, mock_service_class, mock_service):
        """Test getting a non-existent water heater."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.get_water_heater = AsyncMock(return_value=None)
        
        # Make request
        response = client.get("/api/v1/water-heaters/nonexistent")
        
        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Verify service was called
        mock_service.get_water_heater.assert_called_once_with("nonexistent")
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_create_water_heater(self, mock_service_class, mock_service, sample_water_heater):
        """Test creating a water heater."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.create_water_heater = AsyncMock(return_value=sample_water_heater)
        
        # Make request
        response = client.post(
            "/api/v1/water-heaters",
            json={
                "name": sample_water_heater.name,
                "model": sample_water_heater.model,
                "manufacturer": sample_water_heater.manufacturer,
                "target_temperature": sample_water_heater.target_temperature,
                "current_temperature": sample_water_heater.current_temperature,
                "status": sample_water_heater.status.value,
                "mode": sample_water_heater.mode.value,
                "health_status": sample_water_heater.health_status
            }
        )
        
        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == sample_water_heater.id
        assert data["name"] == sample_water_heater.name
        
        # Verify service was called
        mock_service.create_water_heater.assert_called_once()
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_update_temperature(self, mock_service_class, mock_service, sample_water_heater):
        """Test updating a water heater's temperature."""
        # Setup mock
        mock_service_class.return_value = mock_service
        updated_heater = sample_water_heater.model_copy(deep=True)
        updated_heater.target_temperature = 55.0
        mock_service.update_target_temperature = AsyncMock(return_value=updated_heater)
        
        # Make request
        response = client.patch(
            f"/api/v1/water-heaters/{sample_water_heater.id}/temperature",
            json={"temperature": 55.0}
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_water_heater.id
        assert data["target_temperature"] == 55.0
        
        # Verify service was called
        mock_service.update_target_temperature.assert_called_once_with(sample_water_heater.id, 55.0)
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_update_mode(self, mock_service_class, mock_service, sample_water_heater):
        """Test updating a water heater's mode."""
        # Setup mock
        mock_service_class.return_value = mock_service
        updated_heater = sample_water_heater.model_copy(deep=True)
        updated_heater.mode = WaterHeaterMode.ECO
        mock_service.update_mode = AsyncMock(return_value=updated_heater)
        
        # Make request
        response = client.patch(
            f"/api/v1/water-heaters/{sample_water_heater.id}/mode",
            json={"mode": "ECO"}
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_water_heater.id
        assert data["mode"] == "ECO"
        
        # Verify service was called
        mock_service.update_mode.assert_called_once()
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_get_health_configuration(self, mock_service_class, mock_service, sample_health_config):
        """Test getting health configuration."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.repository.get_health_configuration = AsyncMock(return_value=sample_health_config)
        
        # Make request
        response = client.get("/api/v1/water-heaters/health-configuration")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "temperature_high" in data
        assert data["temperature_high"]["threshold"] == 70.0
        assert data["temperature_high"]["status"] == "RED"
        
        # Verify service was called
        mock_service.repository.get_health_configuration.assert_called_once()
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_set_health_configuration(self, mock_service_class, mock_service, sample_health_config):
        """Test setting health configuration."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.repository.set_health_configuration = AsyncMock()
        mock_service.repository.get_health_configuration = AsyncMock(return_value=sample_health_config)
        
        # Make request
        response = client.post(
            "/api/v1/water-heaters/health-configuration",
            json=sample_health_config
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "temperature_high" in data
        
        # Verify service was called
        mock_service.repository.set_health_configuration.assert_called_once_with(sample_health_config)
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_get_alert_rules(self, mock_service_class, mock_service, sample_alert_rule):
        """Test getting alert rules."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.repository.get_alert_rules = AsyncMock(return_value=[sample_alert_rule])
        
        # Make request
        response = client.get("/api/v1/water-heaters/alert-rules")
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_alert_rule["name"]
        
        # Verify service was called
        mock_service.repository.get_alert_rules.assert_called_once()
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_add_alert_rule(self, mock_service_class, mock_service, sample_alert_rule):
        """Test adding an alert rule."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.repository.add_alert_rule = AsyncMock(return_value=sample_alert_rule)
        
        # Make request
        response = client.post(
            "/api/v1/water-heaters/alert-rules",
            json=sample_alert_rule
        )
        
        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_alert_rule["name"]
        assert data["id"] == sample_alert_rule["id"]
        
        # Verify service was called
        mock_service.repository.add_alert_rule.assert_called_once_with(sample_alert_rule)
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_update_alert_rule(self, mock_service_class, mock_service, sample_alert_rule):
        """Test updating an alert rule."""
        # Setup mock
        mock_service_class.return_value = mock_service
        updated_rule = {**sample_alert_rule, "severity": "CRITICAL", "enabled": False}
        mock_service.repository.update_alert_rule = AsyncMock(return_value=updated_rule)
        
        # Make request
        response = client.put(
            f"/api/v1/water-heaters/alert-rules/{sample_alert_rule['id']}",
            json=updated_rule
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["severity"] == "CRITICAL"
        assert data["enabled"] == False
        
        # Verify service was called
        mock_service.repository.update_alert_rule.assert_called_once_with(sample_alert_rule["id"], updated_rule)
    
    @patch("src.api.water_heater.configurable_router.ConfigurableWaterHeaterService")
    def test_delete_alert_rule(self, mock_service_class, mock_service, sample_alert_rule):
        """Test deleting an alert rule."""
        # Setup mock
        mock_service_class.return_value = mock_service
        mock_service.repository.delete_alert_rule = AsyncMock(return_value=True)
        
        # Make request
        response = client.delete(f"/api/v1/water-heaters/alert-rules/{sample_alert_rule['id']}")
        
        # Verify
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify service was called
        mock_service.repository.delete_alert_rule.assert_called_once_with(sample_alert_rule["id"])
