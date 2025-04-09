#!/usr/bin/env python3
"""
Test for the integration between Asset DB and Device Shadow systems.
Following TDD principles, these tests define the expected behavior before implementation.
"""
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.services.asset_registry import AssetRegistryService

# Import the services we'll be using/creating
from src.services.device_shadow import DeviceShadowService, InMemoryShadowStorage


class TestDeviceDataIntegration:
    """Tests for the integration between Asset DB and Device Shadow."""

    @pytest.fixture
    async def shadow_service(self):
        """Create a shadow service for testing."""
        # Create a mock event bus
        mock_event_bus = MagicMock()
        mock_event_bus.publish = asyncio.coroutine(lambda topic, data: None)

        # Create the service with in-memory storage
        service = DeviceShadowService(
            storage_provider=InMemoryShadowStorage(), event_bus=mock_event_bus
        )
        return service

    @pytest.fixture
    async def asset_service(self):
        """Create an asset registry service for testing."""
        # We'll implement this fixture once we create the service
        service = AssetRegistryService(db_connection=None)  # Mock DB connection
        return service

    @pytest.mark.asyncio
    async def test_device_data_separation(self, shadow_service, asset_service):
        """
        Test that device metadata is stored in Asset DB and state data is in Shadow.

        This test verifies:
        1. Static metadata is stored in the Asset DB
        2. Only state data is in the shadow document
        3. Asset DB changes trigger shadow metadata updates
        """
        # 1. Create a test device in the Asset DB
        device_id = "wh-test-001"
        device_metadata = {
            "device_id": device_id,
            "device_type": "water_heater",
            "manufacturer": "AquaTech",
            "model": "HeatMaster 5000",
            "serial_number": "AT-HM5K-12345",
            "installation_date": datetime.utcnow().isoformat(),
            "location": {"building": "Main Campus", "floor": "3", "room": "304B"},
            "specifications": {"capacity": "80", "voltage": "240", "wattage": "4500"},
        }

        await asset_service.register_device(device_metadata)

        # 2. Create a shadow document with only state data
        device_state = {
            "temperature": "140",
            "temperature_unit": "F",
            "pressure": "45",
            "pressure_unit": "PSI",
            "heating_element": "active",
            "water_level": "75",
            "water_level_unit": "%",
        }

        await shadow_service.create_device_shadow(
            device_id=device_id, reported_state=device_state
        )

        # 3. Verify the shadow contains only state data and device ID
        shadow = await shadow_service.get_device_shadow(device_id)
        assert "device_id" in shadow
        assert "reported" in shadow
        assert "temperature" in shadow["reported"]

        # 4. Verify no metadata exists in the shadow document
        assert "manufacturer" not in shadow
        assert "model" not in shadow
        assert "location" not in shadow
        assert "specifications" not in shadow

        # 5. Update device location in Asset DB
        new_location = {"building": "Main Campus", "floor": "4", "room": "401A"}
        await asset_service.update_device_location(device_id, new_location)

        # 6. Verify location is updated in Asset DB but not in shadow
        device_info = await asset_service.get_device_info(device_id)
        assert device_info["location"]["room"] == "401A"

        # 7. Verify shadow document has not been polluted with location data
        shadow = await shadow_service.get_device_shadow(device_id)
        assert "location" not in shadow

    @pytest.mark.asyncio
    async def test_combined_device_view(self, shadow_service, asset_service):
        """
        Test that we can get a combined view of device with both metadata and state.

        This verifies:
        1. We can retrieve a unified view of the device
        2. The unified view contains both metadata and state
        3. The data sources are properly combined
        """
        # 1. Setup test data (same as previous test)
        device_id = "wh-test-002"

        # Create device in Asset DB
        device_metadata = {
            "device_id": device_id,
            "device_type": "water_heater",
            "manufacturer": "HydroTech",
            "model": "WaterWarmer Pro",
            "serial_number": "HT-WWP-54321",
            "installation_date": datetime.utcnow().isoformat(),
            "location": {"building": "East Wing", "floor": "2", "room": "201"},
            "specifications": {"capacity": "50", "voltage": "120", "wattage": "3500"},
        }

        await asset_service.register_device(device_metadata)

        # Create shadow document
        device_state = {
            "temperature": "135",
            "temperature_unit": "F",
            "pressure": "40",
            "pressure_unit": "PSI",
            "heating_element": "standby",
            "water_level": "90",
            "water_level_unit": "%",
        }

        await shadow_service.create_device_shadow(
            device_id=device_id, reported_state=device_state
        )

        # 2. Get unified device view
        unified_view = await asset_service.get_unified_device_view(device_id)

        # 3. Verify the unified view contains both metadata and state
        assert unified_view["device_id"] == device_id
        assert unified_view["manufacturer"] == "HydroTech"
        assert unified_view["location"]["room"] == "201"
        assert unified_view["specifications"]["capacity"] == "50"
        assert unified_view["state"]["temperature"] == "135"
        assert unified_view["state"]["heating_element"] == "standby"

        # 4. Update state in the shadow document
        new_state = {"temperature": "142", "heating_element": "active"}

        await shadow_service.update_device_shadow_reported(
            device_id=device_id, reported_state=new_state, merge=True
        )

        # 5. Verify the unified view reflects updated state
        updated_view = await asset_service.get_unified_device_view(device_id)
        assert updated_view["state"]["temperature"] == "142"
        assert updated_view["state"]["heating_element"] == "active"
        assert updated_view["state"]["water_level"] == "90"  # Unchanged values persist

    @pytest.mark.asyncio
    async def test_metadata_change_notification(self, shadow_service, asset_service):
        """
        Test that metadata changes in Asset DB trigger notifications.

        This verifies:
        1. Changes to device metadata in Asset DB trigger events
        2. These events can be consumed by interested systems
        """
        # 1. Setup test data
        device_id = "wh-test-003"

        # Create device in Asset DB with event listener mock
        device_metadata = {
            "device_id": device_id,
            "device_type": "water_heater",
            "manufacturer": "ThermalCorp",
            "model": "HeatWave 200",
            "firmware_version": "1.0.3",
        }

        # Mock event handler
        event_handler = MagicMock()
        asset_service.subscribe_to_metadata_changes(event_handler)

        # Register device
        await asset_service.register_device(device_metadata)

        # 2. Update firmware version
        await asset_service.update_device_firmware(
            device_id=device_id, new_version="1.1.0"
        )

        # 3. Verify event handler was called with appropriate data
        event_handler.assert_called_with(
            {
                "device_id": device_id,
                "change_type": "firmware_update",
                "old_value": "1.0.3",
                "new_value": "1.1.0",
                "timestamp": pytest.approx(datetime.utcnow().timestamp(), abs=5),
            }
        )
