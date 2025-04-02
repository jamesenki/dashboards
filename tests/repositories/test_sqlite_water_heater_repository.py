"""
Tests for the SQLite implementation of the water heater repository.
"""
import pytest
import asyncio
import sqlite3
from datetime import datetime, timedelta
import uuid
from typing import Optional, List

from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterStatus,
    WaterHeaterReading,
    WaterHeaterDiagnosticCode
)
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository
from src.utils.database import get_db_connection


class TestSQLiteWaterHeaterRepository:
    """Tests for the SQLite water heater repository."""
    
    @pytest.fixture
    def test_db_path(self):
        return ":memory:"
    
    @pytest.fixture
    def repository(self, test_db_path):
        # Create in-memory database for testing
        repo = SQLiteWaterHeaterRepository(db_path=test_db_path)
        
        # Initialize DB schema
        with get_db_connection(test_db_path) as conn:
            # Create tables if they don't exist
            repo._create_tables(conn)
        
        return repo
    
    @pytest.fixture
    def sample_water_heater(self):
        """Create a sample water heater for testing."""
        return WaterHeater(
            id="wh-test-123",
            name="Test Water Heater",
            model="EcoHeat 2000",
            manufacturer="WaterTech Inc.",
            current_temperature=45.5,
            target_temperature=50.0,
            status=WaterHeaterStatus.IDLE,
            mode=WaterHeaterMode.NORMAL,
            installation_date=datetime.now() - timedelta(days=365),
            last_maintenance=datetime.now() - timedelta(days=30),
            warranty_expiry=datetime.now() + timedelta(days=730),
            health_status="GREEN",
            readings=[],
            diagnostic_codes=[]
        )
    
    @pytest.fixture
    def sample_reading(self):
        """Create a sample reading for testing."""
        return WaterHeaterReading(
            id=str(uuid.uuid4()),
            temperature=45.5,
            pressure=4.2,
            energy_usage=500.0,
            flow_rate=2.5,
            timestamp=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_get_water_heaters_empty(self, repository):
        """Test retrieving water heaters from an empty repository."""
        result = await repository.get_water_heaters()
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_create_and_get_water_heater(self, repository, sample_water_heater):
        """Test creating and retrieving a water heater."""
        # Create water heater
        created = await repository.create_water_heater(sample_water_heater)
        assert created.id == sample_water_heater.id
        assert created.name == sample_water_heater.name
        
        # Get all water heaters
        all_heaters = await repository.get_water_heaters()
        assert len(all_heaters) == 1
        assert all_heaters[0].id == sample_water_heater.id
        
        # Get specific water heater
        retrieved = await repository.get_water_heater(sample_water_heater.id)
        assert retrieved is not None
        assert retrieved.id == sample_water_heater.id
        assert retrieved.name == sample_water_heater.name
        assert retrieved.model == sample_water_heater.model
        assert retrieved.health_status == "GREEN"
    
    @pytest.mark.asyncio
    async def test_update_water_heater(self, repository, sample_water_heater):
        """Test updating a water heater."""
        # Create water heater
        await repository.create_water_heater(sample_water_heater)
        
        # Update properties
        updates = {
            "name": "Updated Heater Name",
            "target_temperature": 55.0,
            "mode": WaterHeaterMode.ECO,
            "health_status": "YELLOW"
        }
        
        updated = await repository.update_water_heater(sample_water_heater.id, updates)
        assert updated.name == "Updated Heater Name"
        assert updated.target_temperature == 55.0
        assert updated.mode == WaterHeaterMode.ECO
        assert updated.health_status == "YELLOW"
        
        # Verify persistence
        retrieved = await repository.get_water_heater(sample_water_heater.id)
        assert retrieved.name == "Updated Heater Name"
        assert retrieved.target_temperature == 55.0
        assert retrieved.mode == WaterHeaterMode.ECO
        assert retrieved.health_status == "YELLOW"
    
    @pytest.mark.asyncio
    async def test_add_reading(self, repository, sample_water_heater, sample_reading):
        """Test adding a reading to a water heater."""
        # Create water heater
        await repository.create_water_heater(sample_water_heater)
        
        # Add reading
        updated = await repository.add_reading(sample_water_heater.id, sample_reading)
        assert updated.id == sample_water_heater.id
        assert len(updated.readings) == 1
        assert updated.readings[0].id == sample_reading.id
        assert updated.readings[0].temperature == sample_reading.temperature
        
        # Current temperature should be updated to match reading
        assert updated.current_temperature == sample_reading.temperature
        
        # Get readings
        readings = await repository.get_readings(sample_water_heater.id)
        assert len(readings) == 1
        assert readings[0].id == sample_reading.id
    
    @pytest.mark.asyncio
    async def test_add_multiple_readings(self, repository, sample_water_heater, sample_reading):
        """Test adding multiple readings and retrieving with limit."""
        # Create water heater
        await repository.create_water_heater(sample_water_heater)
        
        # Add 5 readings
        for i in range(5):
            reading = WaterHeaterReading(
                id=str(uuid.uuid4()),
                temperature=45.0 + i,
                pressure=4.0 + (i * 0.1),
                energy_usage=500.0 + (i * 50),
                flow_rate=2.0 + (i * 0.1),
                timestamp=datetime.now() - timedelta(hours=i)
            )
            await repository.add_reading(sample_water_heater.id, reading)
        
        # Get all readings
        all_readings = await repository.get_readings(sample_water_heater.id)
        assert len(all_readings) == 5
        
        # Get limited readings
        limited_readings = await repository.get_readings(sample_water_heater.id, limit=3)
        assert len(limited_readings) == 3
        
        # Readings should be in reverse chronological order (newest first)
        assert limited_readings[0].temperature > limited_readings[1].temperature
    
    @pytest.mark.asyncio
    async def test_nonexistent_water_heater(self, repository):
        """Test operations on a non-existent water heater."""
        nonexistent_id = "wh-nonexistent"
        
        # Get should return None
        result = await repository.get_water_heater(nonexistent_id)
        assert result is None
        
        # Update should return None
        result = await repository.update_water_heater(nonexistent_id, {"name": "New Name"})
        assert result is None
        
        # Add reading should return None
        reading = WaterHeaterReading(
            id=str(uuid.uuid4()),
            temperature=50.0,
            timestamp=datetime.now()
        )
        result = await repository.add_reading(nonexistent_id, reading)
        assert result is None
        
        # Get readings should return empty list
        readings = await repository.get_readings(nonexistent_id)
        assert isinstance(readings, list)
        assert len(readings) == 0
    
    @pytest.mark.asyncio
    async def test_get_water_heater_health_configuration(self, repository):
        """Test retrieving health configuration for water heaters."""
        # Initially should be empty
        config = await repository.get_health_configuration()
        assert isinstance(config, dict)
        
        # Add some configuration and test retrieval
        await repository.set_health_configuration({
            "temperature_high": {"threshold": 70.0, "status": "RED"},
            "temperature_warning": {"threshold": 65.0, "status": "YELLOW"},
            "pressure_high": {"threshold": 6.0, "status": "RED"}
        })
        
        config = await repository.get_health_configuration()
        assert "temperature_high" in config
        assert config["temperature_high"]["threshold"] == 70.0
        assert config["temperature_high"]["status"] == "RED"
        assert config["temperature_warning"]["status"] == "YELLOW"
    
    @pytest.mark.asyncio
    async def test_get_alert_rules(self, repository):
        """Test retrieving alert rules for water heaters."""
        # Initially should be empty
        rules = await repository.get_alert_rules()
        assert isinstance(rules, list)
        assert len(rules) == 0
        
        # Add some rules and test retrieval
        rule1 = {
            "id": "rule1",
            "name": "High Temperature Alert",
            "condition": "temperature > 75",
            "severity": "HIGH",
            "message": "Water heater temperature exceeds safe level",
            "enabled": True
        }
        
        rule2 = {
            "id": "rule2",
            "name": "Pressure Warning",
            "condition": "pressure > 5.5",
            "severity": "MEDIUM",
            "message": "Water heater pressure is high",
            "enabled": True
        }
        
        await repository.add_alert_rule(rule1)
        await repository.add_alert_rule(rule2)
        
        rules = await repository.get_alert_rules()
        assert len(rules) == 2
        assert rules[0]["name"] == "High Temperature Alert"
        assert rules[1]["name"] == "Pressure Warning"
        
        # Update a rule
        rule1_update = {**rule1, "severity": "CRITICAL", "enabled": False}
        await repository.update_alert_rule(rule1["id"], rule1_update)
        
        rules = await repository.get_alert_rules()
        updated_rule = next((r for r in rules if r["id"] == "rule1"), None)
        assert updated_rule is not None
        assert updated_rule["severity"] == "CRITICAL"
        assert updated_rule["enabled"] is False
        
        # Delete a rule
        await repository.delete_alert_rule("rule2")
        rules = await repository.get_alert_rules()
        assert len(rules) == 1
        assert rules[0]["id"] == "rule1"
