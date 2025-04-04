"""
Test cases for database schema updates to support Rheem water heaters.
Following TDD principles, we write tests before implementation.
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.db.models import Base

# Import the Rheem water heater models from the correct location
from src.db.models.rheem_water_heater import (
    RheemWaterHeaterModel,
    RheemWaterHeaterSeries,
    RheemWaterHeaterTelemetry,
)


class TestRheemWaterHeaterSchema:
    """Test cases for updated database schema for Rheem water heaters."""

    @pytest.fixture
    def test_db(self):
        """Create test database with schema."""
        # Create in-memory SQLite database for testing
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def session(self, test_db):
        """Create test session."""
        with Session(test_db) as session:
            yield session

    def test_water_heater_series_schema(self, session):
        """Test that WaterHeaterSeries can store Rheem series."""
        # Create Rheem series
        series = WaterHeaterSeries(
            manufacturer="Rheem",
            name="ProTerra",
            description="Flagship hybrid electric heat pump water heater",
            type=WaterHeaterType.HYBRID,
            tier="premium",
            features={
                "uef_rating": 4.0,
                "eco_net_enabled": True,
                "leak_guard": True,
                "warranty_years": 10,
                "operation_modes": [
                    "Energy Saver",
                    "Heat Pump",
                    "Electric",
                    "High Demand",
                    "Vacation",
                ],
            },
        )
        session.add(series)
        session.commit()

        # Retrieve and verify
        result = session.execute(select(WaterHeaterSeries)).scalar_one()
        assert result.manufacturer == "Rheem"
        assert result.name == "ProTerra"
        assert result.type == WaterHeaterType.HYBRID
        assert result.tier == "premium"
        assert "uef_rating" in result.features
        assert result.features["uef_rating"] == 4.0
        assert "operation_modes" in result.features
        assert len(result.features["operation_modes"]) == 5
        assert "Energy Saver" in result.features["operation_modes"]

    def test_water_heater_model_schema(self, session):
        """Test that WaterHeaterModel can store Rheem model details."""
        # Create Rheem series first
        series = WaterHeaterSeries(
            manufacturer="Rheem",
            name="Professional",
            description="High-quality models sold through contractors",
            type=WaterHeaterType.TANK,
            tier="professional",
        )
        session.add(series)
        session.flush()

        # Create Rheem model
        model = WaterHeaterModel(
            series_id=series.id,
            model_number="PROTH50 T2 RH350",
            name="Professional 50-Gallon Electric Water Heater",
            capacity=50.0,
            energy_star_certified=True,
            smart_features=True,
            eco_net_compatible=True,
            wifi_module_included=True,
            leak_detection=True,
            heating_elements=2,
            max_temperature=85.0,
            first_hour_rating=70.0,
            recovery_rate=21.0,
            uef_rating=3.75,
            warranty_info={
                "tank": 12,
                "parts": 5,
                "labor": 1,
            },
            specifications={
                "height_inches": 61.25,
                "diameter_inches": 22.25,
                "weight_lbs": 196,
                "voltage": 240,
                "wattage": 4500,
            },
        )
        session.add(model)
        session.commit()

        # Retrieve and verify
        result = session.execute(select(WaterHeaterModel)).scalar_one()
        assert result.model_number == "PROTH50 T2 RH350"
        assert result.capacity == 50.0
        assert result.energy_star_certified is True
        assert result.smart_features is True
        assert result.eco_net_compatible is True
        assert result.leak_detection is True
        assert result.uef_rating == 3.75
        assert result.warranty_info["tank"] == 12
        assert result.specifications["height_inches"] == 61.25

    def test_water_heater_telemetry_schema(self, session):
        """Test that WaterHeaterTelemetry can store Rheem telemetry data."""
        # Create series and model first
        series = WaterHeaterSeries(
            manufacturer="Rheem",
            name="Performance Platinum",
            type=WaterHeaterType.TANKLESS,
        )
        session.add(series)
        session.flush()

        model = WaterHeaterModel(
            series_id=series.id,
            model_number="RTGH-95DVLN",
            name="Performance Platinum 9.5 GPM Natural Gas Tankless Water Heater",
        )
        session.add(model)
        session.flush()

        # Create Rheem telemetry
        telemetry = WaterHeaterTelemetry(
            device_id="rheem-device-123",
            model_id=model.id,
            timestamp=1617211200,  # Unix timestamp
            temperature=49.5,
            set_point=50.0,
            heating_active=True,
            flow_rate=6.2,
            inlet_temp=15.5,
            outlet_temp=48.5,
            power_consumption=4200.0,
            mode="HEAT_PUMP",
            # Rheem-specific telemetry fields
            ambient_temp=22.5,
            humidity=45.0,
            compressor_active=True,
            heating_element_active=False,
            wifi_signal_strength=78,
            error_codes={"E01": "Low voltage detected"},
            energy_usage_day=12.5,
            power_source="HEAT_PUMP",
            total_energy_used=1580.25,
            operating_cost=0.185,  # cost per kWh
            estimated_savings=2.75,  # daily savings compared to standard
        )
        session.add(telemetry)
        session.commit()

        # Retrieve and verify
        result = session.execute(select(WaterHeaterTelemetry)).scalar_one()
        assert result.device_id == "rheem-device-123"
        assert result.temperature == 49.5
        assert result.set_point == 50.0
        assert result.flow_rate == 6.2
        assert result.inlet_temp == 15.5
        assert result.outlet_temp == 48.5
        assert result.mode == "HEAT_PUMP"
        assert result.ambient_temp == 22.5
        assert result.humidity == 45.0
        assert result.compressor_active is True
        assert result.heating_element_active is False
        assert result.wifi_signal_strength == 78
        assert "E01" in result.error_codes
        assert result.energy_usage_day == 12.5
        assert result.power_source == "HEAT_PUMP"
        assert result.operating_cost == 0.185
