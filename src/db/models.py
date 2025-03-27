import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()


class DeviceModel(Base):
    __tablename__ = "devices"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="offline")
    location = Column(String, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    properties = Column(JSON, nullable=False, default={})  # Changed from "metadata" to "properties"
    
    readings = relationship("ReadingModel", back_populates="device", cascade="all, delete")
    diagnostic_codes = relationship("DiagnosticCodeModel", back_populates="device", cascade="all, delete")


class ReadingModel(Base):
    __tablename__ = "readings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, primary_key=True, nullable=False, default=datetime.utcnow)
    metric_name = Column(String, nullable=False)
    value = Column(JSON, nullable=False)  # Store any type as JSON
    unit = Column(String, nullable=True)
    
    device = relationship("DeviceModel", back_populates="readings")
    
    # Set table arguments for PostgreSQL partitioning
    __table_args__ = (
        # No more partition hints since we're making a regular table now
    )


class DiagnosticCodeModel(Base):
    __tablename__ = "diagnostic_codes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # Info, Warning, Critical, Maintenance
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    active = Column(Boolean, nullable=False, default=True)
    additional_info = Column(JSON, nullable=True)  # Additional data related to the diagnostic code
    
    device = relationship("DeviceModel", back_populates="diagnostic_codes")
