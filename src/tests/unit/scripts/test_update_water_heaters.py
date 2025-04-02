"""
Unit tests for the water heater update script.
Following TDD principles, we're writing tests before running the script.
"""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.db.models import DeviceModel, DiagnosticCodeModel
from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import WaterHeaterType
from src.scripts.update_water_heaters import (
    add_new_water_heaters,
    update_existing_water_heaters,
)


@pytest.mark.asyncio
async def test_update_existing_water_heaters():
    """Test updating existing water heaters with new fields."""
    # Mock the database session
    mock_device1 = MagicMock()
    mock_device1.id = "wh-test-1"
    mock_device1.properties = {"capacity": 120}  # Residential based on capacity

    mock_device2 = MagicMock()
    mock_device2.id = "wh-test-2"
    mock_device2.properties = {"capacity": 200}  # Commercial based on capacity

    mock_device3 = MagicMock()
    mock_device3.id = "wh-test-3"
    mock_device3.properties = {}  # No capacity, will be randomly assigned

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        mock_device1,
        mock_device2,
        mock_device3,
    ]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session_generator = AsyncMock()
    mock_session_generator.__aiter__.return_value = [mock_session]

    # Patch the database session
    with patch(
        "src.scripts.update_water_heaters.get_db_session",
        return_value=mock_session_generator,
    ):
        # Patch random to make tests deterministic
        with patch(
            "src.scripts.update_water_heaters.random.random", return_value=0.2
        ):  # Will make random devices residential
            with patch(
                "src.scripts.update_water_heaters.random.sample",
                return_value=[
                    {
                        "code": "R001",
                        "description": "High temperature warning",
                        "severity": "Warning",
                    },
                    {
                        "code": "R002",
                        "description": "Critical high temperature",
                        "severity": "Critical",
                    },
                ],
            ):
                with patch(
                    "src.scripts.update_water_heaters.random.randint", return_value=2
                ):
                    await update_existing_water_heaters()

    # Verify that devices were updated correctly
    assert mock_device1.properties["heater_type"] == WaterHeaterType.RESIDENTIAL
    assert (
        mock_device1.properties["specification_link"]
        == "/docs/specifications/water_heaters/residential.md"
    )

    assert mock_device2.properties["heater_type"] == WaterHeaterType.COMMERCIAL
    assert (
        mock_device2.properties["specification_link"]
        == "/docs/specifications/water_heaters/commercial.md"
    )

    assert (
        mock_device3.properties["heater_type"] == WaterHeaterType.COMMERCIAL
    )  # When random.random() returns 0.2, which is < 0.3, it's commercial
    assert (
        mock_device3.properties["specification_link"]
        == "/docs/specifications/water_heaters/commercial.md"
    )

    # Verify that diagnostic codes were added
    assert mock_session.add.call_count >= 6  # 2 codes for each of 3 devices
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_add_new_water_heaters():
    """Test adding new water heaters."""
    # Mock generate_water_heaters to return a fixed set of test heaters
    mock_heater1 = MagicMock()
    mock_heater1.id = "wh-new-1"
    mock_heater1.name = "Test Commercial Heater"
    mock_heater1.type = DeviceType.WATER_HEATER
    mock_heater1.status = DeviceStatus.ONLINE
    mock_heater1.heater_type = WaterHeaterType.COMMERCIAL
    mock_heater1.specification_link = "/docs/specifications/water_heaters/commercial.md"
    mock_heater1.diagnostic_codes = [
        {
            "code": "C001",
            "description": "High temperature warning",
            "severity": "Warning",
            "timestamp": datetime.now(),
            "active": True,
        }
    ]

    mock_heater2 = MagicMock()
    mock_heater2.id = "wh-new-2"
    mock_heater2.name = "Test Residential Heater"
    mock_heater2.type = DeviceType.WATER_HEATER
    mock_heater2.status = DeviceStatus.ONLINE
    mock_heater2.heater_type = WaterHeaterType.RESIDENTIAL
    mock_heater2.specification_link = (
        "/docs/specifications/water_heaters/residential.md"
    )
    mock_heater2.diagnostic_codes = [
        {
            "code": "R001",
            "description": "High temperature warning",
            "severity": "Warning",
            "timestamp": datetime.now(),
            "active": True,
        }
    ]

    # Mock session for database operations
    mock_session = AsyncMock()
    mock_session_generator = AsyncMock()
    mock_session_generator.__aiter__.return_value = [mock_session]

    # Patch functions
    with patch(
        "src.scripts.update_water_heaters.get_db_session",
        return_value=mock_session_generator,
    ):
        with patch(
            "src.scripts.update_water_heaters.generate_water_heaters",
            return_value=[mock_heater1, mock_heater2],
        ):
            with patch(
                "src.scripts.update_water_heaters.jsonable_encoder"
            ) as mock_encoder:
                # Configure jsonable_encoder to return dictionaries with the necessary structure
                def mock_encode(obj):
                    if obj == mock_heater1:
                        return {
                            "id": "wh-new-1",
                            "name": "Test Commercial Heater",
                            "type": DeviceType.WATER_HEATER,
                            "status": DeviceStatus.ONLINE,
                            "target_temperature": 65.0,
                            "current_temperature": 64.2,
                            "min_temperature": 40.0,
                            "max_temperature": 85.0,
                            "mode": "ECO",
                            "heater_status": "STANDBY",
                            "heater_type": WaterHeaterType.COMMERCIAL,
                            "specification_link": "/docs/specifications/water_heaters/commercial.md",
                            "capacity": 1000,
                            "efficiency_rating": 0.95,
                            "readings": [],
                            "diagnostic_codes": [
                                {
                                    "code": "C001",
                                    "description": "High temperature warning",
                                    "severity": "Warning",
                                    "timestamp": datetime.now(),
                                    "active": True,
                                    "additional_info": {"priority": "high"},
                                }
                            ],
                        }
                    else:
                        return {
                            "id": "wh-new-2",
                            "name": "Test Residential Heater",
                            "type": DeviceType.WATER_HEATER,
                            "status": DeviceStatus.ONLINE,
                            "target_temperature": 55.0,
                            "current_temperature": 54.8,
                            "min_temperature": 40.0,
                            "max_temperature": 75.0,
                            "mode": "ECO",
                            "heater_status": "STANDBY",
                            "heater_type": WaterHeaterType.RESIDENTIAL,
                            "specification_link": "/docs/specifications/water_heaters/residential.md",
                            "capacity": 80,
                            "efficiency_rating": 0.88,
                            "readings": [],
                            "diagnostic_codes": [
                                {
                                    "code": "R001",
                                    "description": "High temperature warning",
                                    "severity": "Warning",
                                    "timestamp": datetime.now(),
                                    "active": True,
                                    "additional_info": {"priority": "medium"},
                                }
                            ],
                        }

                mock_encoder.side_effect = mock_encode
                await add_new_water_heaters()

    # Verify devices were added to the database
    assert (
        mock_session.add.call_count >= 4
    )  # 2 devices + at least 1 diagnostic code each
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_main_full_execution():
    """Test the full execution of the script."""
    with patch("src.scripts.update_water_heaters.initialize_db") as mock_init_db:
        with patch(
            "src.scripts.update_water_heaters.update_existing_water_heaters"
        ) as mock_update:
            with patch(
                "src.scripts.update_water_heaters.add_new_water_heaters"
            ) as mock_add:
                from src.scripts.update_water_heaters import main

                await main()

                # Verify all functions were called
                mock_init_db.assert_called_once()
                mock_update.assert_called_once()
                mock_add.assert_called_once()
