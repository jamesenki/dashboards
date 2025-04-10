"""
Integration test for Water Heater Service to Repository Gateway interaction.
Tests the boundary between use cases and repository interfaces following Clean Architecture.

This file demonstrates proper TDD phases with explicit tagging and follows
Clean Architecture principles by testing only the boundary between layers.
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.domain.entities.water_heater import WaterHeater
from src.domain.value_objects.device_status import DeviceStatus
from src.domain.value_objects.temperature import Temperature
from src.use_cases.interfaces.water_heater_repository import WaterHeaterRepository
from src.use_cases.water_heater_service import WaterHeaterService


class InMemoryWaterHeaterRepository(WaterHeaterRepository):
    """In-memory implementation of WaterHeaterRepository for testing.

    This test double implements the repository interface but stores
    data in memory instead of using a database. This isolates the
    test from external dependencies while still testing the repository interface.
    """

    def __init__(self):
        self.heaters = {}

    async def get_by_id(self, heater_id: str) -> WaterHeater:
        """Get a water heater by ID."""
        if heater_id not in self.heaters:
            raise ValueError(f"Water heater with ID {heater_id} not found")
        return self.heaters[heater_id]

    async def get_all(self) -> list[WaterHeater]:
        """Get all water heaters."""
        return list(self.heaters.values())

    async def get_by_manufacturer(self, manufacturer: str) -> list[WaterHeater]:
        """Get water heaters by manufacturer."""
        return [h for h in self.heaters.values() if h.manufacturer == manufacturer]

    async def save(self, heater: WaterHeater) -> WaterHeater:
        """Save a water heater."""
        self.heaters[heater.id] = heater
        return heater

    async def update(self, heater: WaterHeater) -> WaterHeater:
        """Update a water heater."""
        if heater.id not in self.heaters:
            raise ValueError(f"Water heater with ID {heater.id} not found")
        self.heaters[heater.id] = heater
        return heater

    async def delete(self, heater_id: str) -> None:
        """Delete a water heater."""
        if heater_id not in self.heaters:
            raise ValueError(f"Water heater with ID {heater_id} not found")
        del self.heaters[heater_id]


@pytest.fixture
def water_heater_repository():
    """Create a test repository with sample data."""
    repo = InMemoryWaterHeaterRepository()

    # Add sample water heaters
    sample_heaters = [
        WaterHeater(
            id="wh-001",
            name="Main Building Heater",
            manufacturer="AquaTech",
            model="AT-5000",
            current_temperature=Temperature(value=120, unit="F"),
            target_temperature=Temperature(value=125, unit="F"),
            status=DeviceStatus.ONLINE,
            is_simulated=False,
            last_updated=datetime.now(),
        ),
        WaterHeater(
            id="wh-002",
            name="East Wing Heater",
            manufacturer="ThermoPlus",
            model="TP-2000",
            current_temperature=Temperature(value=118, unit="F"),
            target_temperature=Temperature(value=120, unit="F"),
            status=DeviceStatus.ONLINE,
            is_simulated=True,
            last_updated=datetime.now(),
        ),
        WaterHeater(
            id="wh-003",
            name="Backup Heater",
            manufacturer="AquaTech",
            model="AT-3000",
            current_temperature=Temperature(value=0, unit="F"),
            target_temperature=Temperature(value=0, unit="F"),
            status=DeviceStatus.OFFLINE,
            is_simulated=False,
            last_updated=datetime.now(),
        ),
    ]

    for heater in sample_heaters:
        repo.heaters[heater.id] = heater

    return repo


@pytest.fixture
def water_heater_service(water_heater_repository):
    """Create a water heater service with the test repository."""
    return WaterHeaterService(repository=water_heater_repository)


class TestWaterHeaterServiceToRepository:
    """Integration tests for Water Heater Service to Repository interaction.

    These tests validate the boundary between the use case (service) and
    the repository gateway following Clean Architecture principles.
    """

    @pytest.mark.red  # TDD Red phase
    async def test_get_all_water_heaters(
        self, water_heater_service, water_heater_repository
    ):
        """Test retrieving all water heaters through the service.

        RED phase: This test defines the expected behavior between service and repository.
        It validates that the service correctly interacts with the repository interface.

        This tests the boundary between:
        - Use Case Layer: WaterHeaterService
        - Gateway Interface: WaterHeaterRepository
        """
        # Execute
        heaters = await water_heater_service.get_all_water_heaters()

        # Verify
        assert len(heaters) == 3
        assert any(h.id == "wh-001" for h in heaters)
        assert any(h.manufacturer == "AquaTech" for h in heaters)
        assert any(h.manufacturer == "ThermoPlus" for h in heaters)

    @pytest.mark.red  # TDD Red phase
    async def test_get_water_heater_by_id(
        self, water_heater_service, water_heater_repository
    ):
        """Test retrieving a specific water heater by ID.

        RED phase: This test defines the expected behavior for ID-based lookups.

        This tests the boundary between:
        - Use Case Layer: ID-based retrieval logic
        - Gateway Interface: Repository access method
        """
        # Execute
        heater = await water_heater_service.get_water_heater_by_id("wh-001")

        # Verify
        assert heater is not None
        assert heater.id == "wh-001"
        assert heater.name == "Main Building Heater"
        assert heater.manufacturer == "AquaTech"
        assert heater.current_temperature.value == 120

    @pytest.mark.red  # TDD Red phase
    async def test_get_water_heater_by_id_not_found(
        self, water_heater_service, water_heater_repository
    ):
        """Test handling of non-existent water heater lookups.

        RED phase: This test defines expected error handling behavior.

        This tests the boundary between:
        - Use Case Layer: Error handling
        - Gateway Interface: Exception propagation
        """
        # Execute and verify
        with pytest.raises(ValueError):
            await water_heater_service.get_water_heater_by_id("non-existent-id")

    @pytest.mark.red  # TDD Red phase
    async def test_update_water_heater_temperature(
        self, water_heater_service, water_heater_repository
    ):
        """Test updating a water heater's target temperature.

        RED phase: This test defines the expected update behavior.

        This tests the boundary between:
        - Use Case Layer: Business rules for temperature updates
        - Gateway Interface: Update method implementation
        """
        # Setup - get the original heater
        original_heater = await water_heater_service.get_water_heater_by_id("wh-001")
        assert original_heater.target_temperature.value == 125

        # Execute - update temperature
        new_temp = Temperature(value=130, unit="F")
        updated_heater = await water_heater_service.update_target_temperature(
            "wh-001", new_temp
        )

        # Verify the update
        assert updated_heater.id == "wh-001"
        assert updated_heater.target_temperature.value == 130

        # Verify persistence (changes are saved to repository)
        heater_from_repo = await water_heater_repository.get_by_id("wh-001")
        assert heater_from_repo.target_temperature.value == 130

    @pytest.mark.red  # TDD Red phase
    async def test_filter_by_manufacturer(
        self, water_heater_service, water_heater_repository
    ):
        """Test filtering water heaters by manufacturer.

        RED phase: This test defines the expected filtering behavior.

        This tests the boundary between:
        - Use Case Layer: Filtering logic
        - Gateway Interface: Repository query method
        """
        # Execute
        aquatech_heaters = await water_heater_service.get_heaters_by_manufacturer(
            "AquaTech"
        )

        # Verify
        assert len(aquatech_heaters) == 2
        assert all(h.manufacturer == "AquaTech" for h in aquatech_heaters)

        # Check other manufacturer
        thermo_heaters = await water_heater_service.get_heaters_by_manufacturer(
            "ThermoPlus"
        )
        assert len(thermo_heaters) == 1
        assert thermo_heaters[0].manufacturer == "ThermoPlus"

    @pytest.mark.red  # TDD Red phase
    async def test_add_new_water_heater(
        self, water_heater_service, water_heater_repository
    ):
        """Test adding a new water heater.

        RED phase: This test defines the expected creation behavior.

        This tests the boundary between:
        - Use Case Layer: Creation business logic
        - Gateway Interface: Repository save method
        """
        # Setup - create a new water heater
        new_heater = WaterHeater(
            id="wh-004",
            name="New Test Heater",
            manufacturer="TestBrand",
            model="Test-1000",
            current_temperature=Temperature(value=110, unit="F"),
            target_temperature=Temperature(value=115, unit="F"),
            status=DeviceStatus.ONLINE,
            is_simulated=True,
            last_updated=datetime.now(),
        )

        # Execute
        saved_heater = await water_heater_service.add_water_heater(new_heater)

        # Verify
        assert saved_heater.id == "wh-004"
        assert saved_heater.name == "New Test Heater"

        # Verify it was saved to the repository
        all_heaters = await water_heater_repository.get_all()
        assert len(all_heaters) == 4
        assert any(h.id == "wh-004" for h in all_heaters)
