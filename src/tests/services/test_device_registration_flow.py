"""
Tests for device registration, asset creation, and shadow management flow.

Following TDD principles, these tests define the expected behavior of:
1. Device registration and manifest upload
2. Asset database entry creation
3. Shadow document creation
4. Bidirectional state changes (device↔frontend)
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage
from src.models.device import DeviceStatus
from src.services.device_shadow import DeviceShadowService

# Sample device manifests for testing
SAMPLE_MANIFESTS = {
    "thermostat": {
        "device_id": "therm-test-001",
        "manufacturer": "EcoTemp",
        "model": "SmartThermostat-X1",
        "firmware_version": "1.2.3",
        "capabilities": {
            "sensors": ["temperature", "humidity"],
            "actuators": ["heating", "cooling"],
            "settings": ["target_temperature", "mode"],
        },
        "metadata": {
            "location": "Living Room",
            "installation_date": "2025-01-15T00:00:00Z",
        },
    },
    "water_heater": {
        "device_id": "wh-test-001",
        "manufacturer": "AquaSmart",
        "model": "ProHeater-500",
        "firmware_version": "2.1.0",
        "capabilities": {
            "sensors": ["temperature", "pressure", "water_flow"],
            "actuators": ["heating_element", "circulation_pump"],
            "settings": ["target_temperature", "mode", "schedule"],
        },
        "metadata": {
            "location": "Basement",
            "tank_capacity": "50 gallons",
            "installation_date": "2024-12-01T00:00:00Z",
        },
    },
}


@pytest.fixture
def mock_registration_db():
    """Mock device registration database service"""
    mock_reg_db = AsyncMock()

    # Mock device registration
    mock_reg_db.register_device = AsyncMock(return_value=True)

    # Mock getting devices from registration DB
    mock_reg_db.get_device = AsyncMock(
        side_effect=lambda device_id: {
            "device_id": device_id,
            "status": "REGISTERED",
            "registration_time": datetime.utcnow().isoformat(),
        }
    )

    return mock_reg_db


@pytest.fixture
def mock_asset_registry():
    """Mock asset registry service"""
    mock_asset_db = AsyncMock()

    # Storage for mocked assets
    mock_asset_db.assets = {}

    # Mock create_asset method
    async def mock_create_asset(device_id, asset_data):
        mock_asset_db.assets[device_id] = asset_data
        return True

    # Mock get_asset method
    async def mock_get_asset(device_id):
        if device_id in mock_asset_db.assets:
            return mock_asset_db.assets[device_id]
        return None

    mock_asset_db.create_asset = AsyncMock(side_effect=mock_create_asset)
    mock_asset_db.get_asset = AsyncMock(side_effect=mock_get_asset)

    return mock_asset_db


@pytest.fixture
async def shadow_service():
    """Create real shadow service with MongoDB storage for testing"""
    # Use in-memory storage for tests to avoid MongoDB dependency
    from src.services.device_shadow import InMemoryShadowStorage

    storage = InMemoryShadowStorage()
    shadow_service = DeviceShadowService(storage_provider=storage)

    return shadow_service


# Red phase tests - these should fail initially
@pytest.mark.asyncio
async def test_device_manifest_creates_asset_entry(
    mock_registration_db, mock_asset_registry, shadow_service
):
    """Test that uploading a device manifest creates an asset entry"""
    # Arrange
    device_id = "therm-test-001"
    manifest = SAMPLE_MANIFESTS["thermostat"]

    # Mock the device_registry_service
    from src.services.manifest_processor import ManifestProcessor

    # Act - this service doesn't exist yet but we're defining the expected behavior
    manifest_processor = ManifestProcessor(
        registration_service=mock_registration_db,
        asset_registry=mock_asset_registry,
        shadow_service=shadow_service,
    )

    # Process the manifest
    result = await manifest_processor.process_device_manifest(device_id, manifest)

    # Assert
    assert result is True
    mock_asset_registry.create_asset.assert_called_once()

    # Asset should have the metadata from the manifest
    asset_data = mock_asset_registry.assets.get(device_id)
    assert asset_data is not None
    assert asset_data["manufacturer"] == manifest["manufacturer"]
    assert asset_data["model"] == manifest["model"]
    assert asset_data["metadata"]["location"] == manifest["metadata"]["location"]


@pytest.mark.asyncio
async def test_new_asset_creates_shadow_document(
    mock_registration_db, mock_asset_registry, shadow_service
):
    """Test that creating a new asset triggers shadow document creation"""
    # Arrange
    device_id = "wh-test-001"
    manifest = SAMPLE_MANIFESTS["water_heater"]

    # Mock services
    from src.services.manifest_processor import ManifestProcessor

    # Act
    manifest_processor = ManifestProcessor(
        registration_service=mock_registration_db,
        asset_registry=mock_asset_registry,
        shadow_service=shadow_service,
    )

    # Process the manifest
    await manifest_processor.process_device_manifest(device_id, manifest)

    # Assert
    # Should have created a shadow document
    shadow_exists = await shadow_service.storage_provider.shadow_exists(device_id)
    assert shadow_exists is True

    # Shadow document should reflect capabilities
    shadow = await shadow_service.get_device_shadow(device_id)
    assert shadow["device_id"] == device_id
    assert "reported" in shadow
    assert "desired" in shadow


@pytest.mark.asyncio
async def test_device_update_propagates_to_shadow(
    mock_registration_db, mock_asset_registry, shadow_service
):
    """Test that device state updates properly update the shadow document"""
    # Arrange
    device_id = "therm-test-001"
    manifest = SAMPLE_MANIFESTS["thermostat"]

    # Create the shadow first
    await shadow_service.create_device_shadow(
        device_id=device_id,
        reported_state={"temperature": 72, "humidity": 45},
        desired_state={"target_temperature": 74},
    )

    # Mock the device update service
    from src.services.device_update_handler import DeviceUpdateHandler

    # Act - Define the service interface we want
    update_handler = DeviceUpdateHandler(shadow_service=shadow_service)

    # Send a device update
    device_update = {
        "temperature": 73,
        "humidity": 46,
        "status": DeviceStatus.ONLINE.value,
    }

    # Process the update
    await update_handler.handle_device_update(device_id, device_update)

    # Assert
    # Shadow should be updated with the new state
    shadow = await shadow_service.get_device_shadow(device_id)
    assert shadow["reported"]["temperature"] == 73
    assert shadow["reported"]["humidity"] == 46
    assert shadow["reported"]["status"] == DeviceStatus.ONLINE.value


@pytest.mark.asyncio
async def test_frontend_request_creates_pending_state(
    mock_registration_db, mock_asset_registry, shadow_service
):
    """Test that frontend requests for state changes create pending states in the shadow"""
    # Arrange
    device_id = "wh-test-001"

    # Create the shadow first
    await shadow_service.create_device_shadow(
        device_id=device_id,
        reported_state={"temperature": 120, "status": DeviceStatus.ONLINE.value},
        desired_state={"target_temperature": 120},
    )

    # Mock the frontend request handler
    from src.services.frontend_request_handler import FrontendRequestHandler

    # Act - Define the service interface we want
    request_handler = FrontendRequestHandler(shadow_service=shadow_service)

    # Frontend requests a temperature change
    request = {"target_temperature": 130, "mode": "ECO"}

    # Process the request
    await request_handler.handle_state_change_request(device_id, request)

    # Assert
    # Shadow desired state should reflect the request with pending status
    shadow = await shadow_service.get_device_shadow(device_id)
    assert shadow["desired"]["target_temperature"] == 130
    assert shadow["desired"]["mode"] == "ECO"
    # Our implementation sorts the pending list for consistency
    assert sorted(shadow["desired"]["_pending"]) == [
        "mode",
        "target_temperature",
    ]  # Pending status tracked

    # Reported state should remain unchanged
    assert shadow["reported"]["temperature"] == 120


@pytest.mark.asyncio
async def test_device_confirmation_resolves_pending_state(
    mock_registration_db, mock_asset_registry, shadow_service
):
    """Test that device confirmation resolves pending state in the shadow"""
    # Arrange
    device_id = "wh-test-001"

    # Create the shadow with pending desired state
    await shadow_service.create_device_shadow(
        device_id=device_id,
        reported_state={"temperature": 120, "status": DeviceStatus.ONLINE.value},
        desired_state={
            "target_temperature": 130,
            "mode": "ECO",
            "_pending": ["target_temperature", "mode"],
        },
    )

    # Mock the device update handler
    from src.services.device_update_handler import DeviceUpdateHandler

    # Act
    update_handler = DeviceUpdateHandler(shadow_service=shadow_service)

    # Device confirms it has changed to requested state
    device_update = {
        "temperature": 125,  # Starting to rise
        "target_temperature": 130,  # Matches desired
        "mode": "ECO",  # Matches desired
        "status": DeviceStatus.ONLINE.value,
    }

    # Process the confirmation
    await update_handler.handle_device_update(device_id, device_update)

    # Assert
    # Shadow should show target_temperature is no longer pending
    shadow = await shadow_service.get_device_shadow(device_id)
    assert shadow["reported"]["temperature"] == 125
    assert shadow["reported"]["target_temperature"] == 130
    assert shadow["reported"]["mode"] == "ECO"
    assert "_pending" not in shadow["desired"] or not shadow["desired"]["_pending"]
