"""
Unit tests for the remaining water heater update script.
Following TDD principles, we're writing tests before running the script.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.device import DeviceType
from src.models.water_heater import WaterHeaterType
from src.scripts.update_remaining_water_heaters import update_remaining_water_heaters


@pytest.mark.asyncio
async def test_update_remaining_water_heaters():
    """Test updating water heaters without types."""
    # Mock devices - some with and some without heater_type
    mock_device1 = MagicMock()
    mock_device1.id = "wh-test-1"
    mock_device1.name = (
        "Office Boiler Room - HeatMaster 200L"  # Commercial indicator in name
    )
    mock_device1.properties = {"capacity": 100}  # No heater_type yet

    mock_device2 = MagicMock()
    mock_device2.id = "wh-test-2"
    mock_device2.name = (
        "Apartment 101 Bathroom - WaterWarm 50L"  # No commercial indicator
    )
    mock_device2.properties = {"capacity": 50}  # No heater_type yet

    mock_device3 = MagicMock()
    mock_device3.id = "wh-test-3"
    mock_device3.name = (
        "Building A Utility Room - ThermoMax 150L"  # Commercial indicator
    )
    mock_device3.properties = {"capacity": 150}  # No heater_type yet

    # This one already has a heater_type and shouldn't be updated
    mock_device4 = MagicMock()
    mock_device4.id = "wh-test-4"
    mock_device4.name = "House 123 Kitchen - EcoTemp 80L"
    mock_device4.properties = {
        "capacity": 80,
        "heater_type": WaterHeaterType.RESIDENTIAL,
        "specification_link": "/docs/specifications/water_heaters/residential.md",
    }

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        mock_device1,
        mock_device2,
        mock_device3,
        mock_device4,
    ]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session_generator = AsyncMock()
    mock_session_generator.__aiter__.return_value = [mock_session]

    # Patch random.random to make tests deterministic
    with patch(
        "src.scripts.update_remaining_water_heaters.get_db_session",
        return_value=mock_session_generator,
    ):
        with patch(
            "src.scripts.update_remaining_water_heaters.random.random", return_value=0.4
        ):  # > 0.3, so not commercial
            await update_remaining_water_heaters()

    # Verify results
    # Device 1 should be commercial based on name
    assert mock_device1.properties["heater_type"] == WaterHeaterType.COMMERCIAL
    assert (
        mock_device1.properties["specification_link"]
        == "/docs/specifications/water_heaters/commercial.md"
    )

    # Device 2 should be residential based on both name and capacity
    assert mock_device2.properties["heater_type"] == WaterHeaterType.RESIDENTIAL
    assert (
        mock_device2.properties["specification_link"]
        == "/docs/specifications/water_heaters/residential.md"
    )

    # Device 3 should be commercial based on both name and capacity
    assert mock_device3.properties["heater_type"] == WaterHeaterType.COMMERCIAL
    assert (
        mock_device3.properties["specification_link"]
        == "/docs/specifications/water_heaters/commercial.md"
    )

    # Device 4 should not have been modified since it already had a heater_type
    assert mock_device4.properties["heater_type"] == WaterHeaterType.RESIDENTIAL
    assert (
        "capacity" in mock_device4.properties
    )  # Original property should still be there

    # Verify session was committed
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_main_execution():
    """Test the full execution of the script."""
    with patch(
        "src.scripts.update_remaining_water_heaters.update_remaining_water_heaters"
    ) as mock_update:
        from src.scripts.update_remaining_water_heaters import main

        await main()

        # Verify update function was called
        mock_update.assert_called_once()
