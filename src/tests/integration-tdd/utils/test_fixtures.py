"""
Shared test fixtures and utilities for integration tests.
These help maintain test isolation and follow Clean Architecture principles.
"""
import asyncio
import os
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

from src.domain.entities.device_shadow import DeviceShadow
from src.domain.entities.water_heater import WaterHeater
from src.domain.value_objects.device_status import DeviceStatus
from src.domain.value_objects.shadow_state import ShadowState
from src.domain.value_objects.temperature import Temperature


class IntegrationTestConfig:
    """Configuration for integration tests.

    This centralizes test configuration and allows for environment-specific settings.
    """

    # Database configuration - use in-memory or test instance
    DB_TYPE = os.getenv(
        "TEST_DB_TYPE", "in-memory"
    )  # in-memory, postgres-test, mongodb-test
    BROKER_TYPE = os.getenv("TEST_BROKER_TYPE", "mock")  # mock, memory

    # TDD Phase
    TDD_PHASE = os.getenv("TDD_PHASE", "red")  # red, green, refactor

    # Test timeouts
    DEFAULT_TIMEOUT = 2.0  # seconds

    @classmethod
    def is_red_phase(cls) -> bool:
        """Check if tests are running in RED phase."""
        return cls.TDD_PHASE.lower() == "red"

    @classmethod
    def is_green_phase(cls) -> bool:
        """Check if tests are running in GREEN phase."""
        return cls.TDD_PHASE.lower() == "green"

    @classmethod
    def is_refactor_phase(cls) -> bool:
        """Check if tests are running in REFACTOR phase."""
        return cls.TDD_PHASE.lower() == "refactor"


@pytest.fixture
def sample_water_heaters() -> Dict[str, Dict[str, Any]]:
    """Create sample water heater data for testing."""
    return {
        "wh-001": {
            "id": "wh-001",
            "name": "Main Building Water Heater",
            "manufacturer": "AquaTech",
            "model": "AT-5000",
            "current_temperature": 120,
            "target_temperature": 125,
            "status": "ONLINE",
            "is_simulated": False,
            "last_updated": datetime.now().isoformat(),
        },
        "wh-002": {
            "id": "wh-002",
            "name": "East Wing Water Heater",
            "manufacturer": "ThermoPlus",
            "model": "TP-2000",
            "current_temperature": 118,
            "target_temperature": 120,
            "status": "ONLINE",
            "is_simulated": True,
            "last_updated": datetime.now().isoformat(),
        },
        "wh-003": {
            "id": "wh-003",
            "name": "Backup Heater",
            "manufacturer": "AquaTech",
            "model": "AT-3000",
            "current_temperature": 0,
            "target_temperature": 0,
            "status": "OFFLINE",
            "is_simulated": False,
            "last_updated": datetime.now().isoformat(),
        },
    }


@pytest.fixture
def water_heater_entities(sample_water_heaters) -> Dict[str, WaterHeater]:
    """Convert sample data to domain entities."""
    entities = {}
    for heater_id, data in sample_water_heaters.items():
        entities[heater_id] = WaterHeater(
            id=data["id"],
            name=data["name"],
            manufacturer=data["manufacturer"],
            model=data["model"],
            current_temperature=Temperature(
                value=data["current_temperature"], unit="F"
            ),
            target_temperature=Temperature(value=data["target_temperature"], unit="F"),
            status=DeviceStatus(data["status"]),
            is_simulated=data["is_simulated"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )
    return entities


@pytest.fixture
def sample_device_shadows() -> Dict[str, Dict[str, Any]]:
    """Create sample device shadow data for testing."""
    return {
        "test-device-001": {
            "device_id": "test-device-001",
            "reported": {
                "temperature": 120,
                "status": "ONLINE",
                "firmware_version": "v1.2.3",
            },
            "desired": {"target_temperature": 120},
            "version": 1,
            "timestamp": datetime.now().isoformat(),
        },
        "test-device-002": {
            "device_id": "test-device-002",
            "reported": {
                "temperature": 118,
                "status": "ONLINE",
                "firmware_version": "v1.2.3",
            },
            "desired": {"target_temperature": 120},
            "version": 1,
            "timestamp": datetime.now().isoformat(),
        },
    }


@pytest.fixture
def shadow_entities(sample_device_shadows) -> Dict[str, DeviceShadow]:
    """Convert sample shadow data to domain entities."""
    entities = {}
    for device_id, data in sample_device_shadows.items():
        entities[device_id] = DeviceShadow(
            device_id=data["device_id"],
            reported=ShadowState(**data["reported"]),
            desired=ShadowState(**data["desired"]),
            version=data["version"],
            timestamp=data["timestamp"],
        )
    return entities


@pytest.fixture
def mock_message_broker():
    """Create a mock message broker for testing."""
    broker = MagicMock()
    broker.publish = MagicMock()
    broker.subscribe = MagicMock()
    return broker


@pytest.fixture
def mock_database_client():
    """Create a mock database client for testing."""
    client = MagicMock()
    return client


class TestUtility:
    """Utility methods for integration tests."""

    @staticmethod
    async def wait_for_condition(
        condition_func, timeout=IntegrationTestConfig.DEFAULT_TIMEOUT, interval=0.1
    ):
        """Wait for a condition to be true with timeout."""
        start_time = asyncio.get_event_loop().time()
        while True:
            if condition_func():
                return True

            if asyncio.get_event_loop().time() - start_time > timeout:
                return False

            await asyncio.sleep(interval)

    @staticmethod
    def compare_entities(entity1, entity2, fields_to_compare=None):
        """Compare two entities for equality on specified fields."""
        if fields_to_compare is None:
            # Compare all fields that are common to both entities
            fields_to_compare = set(vars(entity1).keys()) & set(vars(entity2).keys())

        for field in fields_to_compare:
            if getattr(entity1, field) != getattr(entity2, field):
                return False

        return True
