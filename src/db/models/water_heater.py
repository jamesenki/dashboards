"""
Database models for water heater information.
"""

from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.db.base import Base


class WaterHeaterType(PyEnum):
    """Types of water heaters."""

    TANK = "tank"
    TANKLESS = "tankless"
    HYBRID = "hybrid"
    SOLAR = "solar"


class WaterHeaterSeries(Base):
    """Water heater product series model."""

    __tablename__ = "water_heater_series"

    id = Column(Integer, primary_key=True)
    manufacturer = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(WaterHeaterType), nullable=False)
    tier = Column(String(50))  # e.g., "entry", "mid", "premium"
    features = Column(JSON)  # Store key features as JSON

    # Relationships
    models = relationship("WaterHeaterModel", back_populates="series")


class WaterHeaterModel(Base):
    """Water heater specific model information."""

    __tablename__ = "water_heater_models"

    id = Column(Integer, primary_key=True)
    model_number = Column(String(100), nullable=False, unique=True)
    series_id = Column(Integer, ForeignKey("water_heater_series.id"))
    name = Column(String(255))
    capacity_gallons = Column(Float)  # For tank-type models
    max_gpm = Column(Float)  # Gallons Per Minute for tankless models
    energy_factor = Column(Float)  # Efficiency rating
    uef = Column(Float)  # Uniform Energy Factor
    btu_input = Column(Integer)  # BTU rating
    recovery_rate = Column(Float)  # Gallons per hour
    first_hour_rating = Column(Float)  # For tank-type models
    dimensions = Column(JSON)  # Store height, width, depth as JSON
    weight = Column(Float)
    warranty_years = Column(Integer)
    is_energy_star = Column(Boolean, default=False)
    is_smart_enabled = Column(Boolean, default=False)
    wifi_enabled = Column(Boolean, default=False)
    leak_detection = Column(Boolean, default=False)
    technical_specs = Column(JSON)  # Additional specifications as JSON

    # Relationships
    series = relationship("WaterHeaterSeries", back_populates="models")
    telemetry = relationship("WaterHeaterTelemetry", back_populates="model")


class WaterHeaterTelemetry(Base):
    """Time-series data from water heater devices."""

    __tablename__ = "water_heater_telemetry"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), nullable=False)
    model_id = Column(Integer, ForeignKey("water_heater_models.id"))
    timestamp = Column(Integer, nullable=False)  # Unix timestamp
    temperature = Column(Float)  # Current water temperature
    set_point = Column(Float)  # Temperature setting
    heating_active = Column(Boolean)
    flow_rate = Column(Float)  # Current water flow rate in GPM
    inlet_temp = Column(Float)  # Inlet water temperature
    outlet_temp = Column(Float)  # Outlet water temperature
    power_consumption = Column(Float)  # In watts
    error_codes = Column(JSON)  # Any active error codes
    mode = Column(String(50))  # e.g., "eco", "high demand", "vacation"

    # Relationships
    model = relationship("WaterHeaterModel", back_populates="telemetry")
