"""
Database models for Rheem water heater information.

These models extend the basic water heater database schema with
Rheem-specific attributes and relationships.
"""

from enum import Enum as PyEnum
from typing import List

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
from src.db.models.water_heater import WaterHeaterType


class RheemProductSeries(PyEnum):
    """Rheem product series categories"""

    # Tank water heaters
    CLASSIC = "Classic"
    CLASSIC_PLUS = "Classic Plus"
    PRESTIGE = "Prestige"
    PROFESSIONAL = "Professional"

    # Tankless water heaters
    PERFORMANCE = "Performance"
    PERFORMANCE_PLATINUM = "Performance Platinum"

    # Hybrid water heaters
    PROTERRA = "ProTerra"


class RheemWaterHeaterMode(PyEnum):
    """Operating modes for Rheem water heaters"""

    OFF = "OFF"
    VACATION = "VACATION"
    ENERGY_SAVER = "ENERGY_SAVER"
    HEAT_PUMP = "HEAT_PUMP"
    ELECTRIC = "ELECTRIC"
    HIGH_DEMAND = "HIGH_DEMAND"


class RheemWaterHeaterSeries(Base):
    """Rheem water heater product series model."""

    __tablename__ = "rheem_water_heater_series"

    id = Column(Integer, primary_key=True)
    manufacturer = Column(String(255), nullable=False, default="Rheem")
    name = Column(Enum(RheemProductSeries), nullable=False)
    description = Column(Text)
    type = Column(Enum(WaterHeaterType), nullable=False)
    tier = Column(String(50))  # e.g., "entry", "mid", "premium"
    features = Column(JSON)  # Store key features as JSON

    # Rheem-specific series attributes
    eco_net_enabled = Column(Boolean, default=False)
    energy_star_certified = Column(Boolean, default=False)
    leak_guard = Column(Boolean, default=False)
    warranty_years = Column(Integer)
    uef_range = Column(JSON)  # Min/max UEF rating as JSON {"min": 2.0, "max": 4.0}
    operation_modes = Column(JSON)  # List of supported modes

    # Relationships
    models = relationship("RheemWaterHeaterModel", back_populates="series")


class RheemWaterHeaterModel(Base):
    """Rheem water heater specific model information."""

    __tablename__ = "rheem_water_heater_models"

    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey("rheem_water_heater_series.id"))
    model_number = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    capacity = Column(Float)  # In gallons
    energy_star_certified = Column(Boolean, default=False)

    # Smart features
    smart_features = Column(Boolean, default=False)
    eco_net_compatible = Column(Boolean, default=False)
    wifi_module_included = Column(Boolean, default=False)
    leak_detection = Column(Boolean, default=False)

    # Technical specifications
    heating_elements = Column(Integer)
    max_temperature = Column(Float)
    first_hour_rating = Column(Float)  # In gallons per hour
    recovery_rate = Column(Float)  # In gallons per hour
    uef_rating = Column(Float)  # Uniform Energy Factor

    # Additional information
    warranty_info = Column(JSON)  # Warranty details as JSON
    specifications = Column(JSON)  # Physical specs, electrical requirements, etc.

    # Relationships
    series = relationship("RheemWaterHeaterSeries", back_populates="models")
    devices = relationship("RheemWaterHeaterDevice", back_populates="model")
    telemetry = relationship("RheemWaterHeaterTelemetry", back_populates="model")


class RheemWaterHeaterDevice(Base):
    """Installed Rheem water heater device information."""

    __tablename__ = "rheem_water_heater_devices"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), nullable=False, unique=True)
    model_id = Column(Integer, ForeignKey("rheem_water_heater_models.id"))
    serial_number = Column(String(100), unique=True)
    installation_date = Column(Integer)  # Unix timestamp
    location = Column(String(255))
    firmware_version = Column(String(50))

    # EcoNet information
    eco_net_enabled = Column(Boolean, default=False)
    wifi_status = Column(String(50))
    last_connected = Column(Integer)  # Unix timestamp
    firmware_up_to_date = Column(Boolean, default=True)

    # Maintenance information
    last_maintenance_date = Column(Integer)  # Unix timestamp
    next_maintenance_date = Column(Integer)  # Unix timestamp - predicted
    anode_rod_replacement_date = Column(Integer)  # Unix timestamp
    descaling_date = Column(Integer)  # Unix timestamp
    warranty_expiration = Column(Integer)  # Unix timestamp

    # Installer information
    installer_info = Column(JSON)  # Contact information for installer

    # Relationships
    model = relationship("RheemWaterHeaterModel", back_populates="devices")
    telemetry = relationship("RheemWaterHeaterTelemetry", back_populates="device")
    maintenance_records = relationship(
        "RheemWaterHeaterMaintenance", back_populates="device"
    )


class RheemWaterHeaterTelemetry(Base):
    """Time-series data from Rheem water heater devices."""

    __tablename__ = "rheem_water_heater_telemetry"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), ForeignKey("rheem_water_heater_devices.device_id"))
    model_id = Column(Integer, ForeignKey("rheem_water_heater_models.id"))
    timestamp = Column(Integer, nullable=False)  # Unix timestamp

    # Basic readings
    temperature = Column(Float)  # Current water temperature
    set_point = Column(Float)  # Target temperature
    heating_active = Column(Boolean)
    flow_rate = Column(Float)  # In gallons per minute

    # Detailed temperature readings
    inlet_temp = Column(Float)
    outlet_temp = Column(Float)
    ambient_temp = Column(Float)

    # Power and energy data
    power_consumption = Column(Float)  # In watts
    power_source = Column(String(50))  # HEAT_PUMP, ELECTRIC, etc.
    energy_usage_day = Column(Float)  # kWh used today
    total_energy_used = Column(Float)  # Cumulative kWh
    operating_cost = Column(Float)  # Current cost per kWh
    estimated_savings = Column(Float)  # Estimated savings compared to standard

    # Operating state
    mode = Column(Enum(RheemWaterHeaterMode))
    humidity = Column(Float)
    compressor_active = Column(Boolean)
    heating_element_active = Column(Boolean)

    # Connectivity
    wifi_signal_strength = Column(Integer)  # As percentage
    eco_net_connected = Column(Boolean)

    # Diagnostic data
    error_codes = Column(JSON)  # Current error codes

    # Relationships
    device = relationship("RheemWaterHeaterDevice", back_populates="telemetry")
    model = relationship("RheemWaterHeaterModel", back_populates="telemetry")


class RheemWaterHeaterMaintenance(Base):
    """Maintenance records for Rheem water heaters."""

    __tablename__ = "rheem_water_heater_maintenance"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), ForeignKey("rheem_water_heater_devices.device_id"))
    timestamp = Column(Integer, nullable=False)  # Unix timestamp
    maintenance_type = Column(String(100))  # e.g., routine, repair, installation
    technician = Column(String(255))
    description = Column(Text)
    actions_taken = Column(JSON)  # List of actions performed
    parts_replaced = Column(JSON)  # List of parts replaced
    readings_before = Column(JSON)  # Readings before maintenance
    readings_after = Column(JSON)  # Readings after maintenance
    next_maintenance_due = Column(
        Integer
    )  # Unix timestamp for next recommended service
    cost = Column(Float)

    # Relationships
    device = relationship(
        "RheemWaterHeaterDevice", back_populates="maintenance_records"
    )
