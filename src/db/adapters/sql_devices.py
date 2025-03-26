from datetime import datetime
from typing import Dict, List, Optional, Union

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.connection import get_db_session
from src.db.models import DeviceModel, ReadingModel
from src.models.device import Device, DeviceReading, DeviceStatus, DeviceType


class SQLDeviceRepository:
    """SQL implementation of device data repository."""

    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def get_devices(
        self,
        type_filter: Optional[DeviceType] = None,
        status_filter: Optional[DeviceStatus] = None,
    ) -> List[Device]:
        """Get devices with optional filtering."""
        query = select(DeviceModel)
        
        if type_filter:
            query = query.where(DeviceModel.type == type_filter)
        
        if status_filter:
            query = query.where(DeviceModel.status == status_filter)
        
        result = await self.session.execute(query)
        db_devices = result.scalars().all()
        
        return [
            Device(
                id=db_device.id,
                name=db_device.name,
                type=db_device.type,
                status=db_device.status,
                location=db_device.location,
                last_seen=db_device.last_seen,
                metadata=db_device.metadata,
                readings=[]  # Don't load all readings by default
            )
            for db_device in db_devices
        ]

    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        query = (
            select(DeviceModel)
            .where(DeviceModel.id == device_id)
        )
        
        result = await self.session.execute(query)
        db_device = result.scalars().first()
        
        if not db_device:
            return None
        
        return Device(
            id=db_device.id,
            name=db_device.name,
            type=db_device.type,
            status=db_device.status,
            location=db_device.location,
            last_seen=db_device.last_seen,
            metadata=db_device.metadata,
            readings=[]  # Don't load all readings by default
        )

    async def create_device(self, device: Device) -> Device:
        """Create a new device."""
        db_device = DeviceModel(
            id=device.id,
            name=device.name,
            type=device.type,
            status=device.status,
            location=device.location,
            last_seen=device.last_seen,
            metadata=device.metadata,
        )
        
        self.session.add(db_device)
        await self.session.commit()
        await self.session.refresh(db_device)
        
        return device

    async def update_device(self, device_id: str, device_data: Dict) -> Optional[Device]:
        """Update a device."""
        query = select(DeviceModel).where(DeviceModel.id == device_id)
        result = await self.session.execute(query)
        db_device = result.scalars().first()
        
        if not db_device:
            return None
        
        for field, value in device_data.items():
            if hasattr(db_device, field):
                setattr(db_device, field, value)
        
        await self.session.commit()
        await self.session.refresh(db_device)
        
        return Device(
            id=db_device.id,
            name=db_device.name,
            type=db_device.type,
            status=db_device.status,
            location=db_device.location,
            last_seen=db_device.last_seen,
            metadata=db_device.metadata,
            readings=[]
        )

    async def delete_device(self, device_id: str) -> bool:
        """Delete a device."""
        query = select(DeviceModel).where(DeviceModel.id == device_id)
        result = await self.session.execute(query)
        db_device = result.scalars().first()
        
        if not db_device:
            return False
        
        await self.session.delete(db_device)
        await self.session.commit()
        
        return True

    async def add_device_reading(self, device_id: str, reading: DeviceReading) -> Optional[Device]:
        """Add a reading to a device."""
        query = select(DeviceModel).where(DeviceModel.id == device_id)
        result = await self.session.execute(query)
        db_device = result.scalars().first()
        
        if not db_device:
            return None
        
        db_reading = ReadingModel(
            device_id=device_id,
            timestamp=reading.timestamp,
            metric_name=reading.metric_name,
            value=reading.value,
            unit=reading.unit,
        )
        
        self.session.add(db_reading)
        
        # Update device's last_seen time
        db_device.last_seen = datetime.now()
        
        await self.session.commit()
        
        # Get updated device with the new reading
        device = Device(
            id=db_device.id,
            name=db_device.name,
            type=db_device.type,
            status=db_device.status,
            location=db_device.location,
            last_seen=db_device.last_seen,
            metadata=db_device.metadata,
            readings=[reading]  # Only include the new reading
        )
        
        return device

    async def get_device_readings(
        self, 
        device_id: str, 
        metric_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[DeviceReading]:
        """Get readings for a device with pagination and filtering."""
        query = (
            select(ReadingModel)
            .where(ReadingModel.device_id == device_id)
            .order_by(ReadingModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        
        if metric_name:
            query = query.where(ReadingModel.metric_name == metric_name)
        
        if start_time:
            query = query.where(ReadingModel.timestamp >= start_time)
        
        if end_time:
            query = query.where(ReadingModel.timestamp <= end_time)
        
        result = await self.session.execute(query)
        db_readings = result.scalars().all()
        
        return [
            DeviceReading(
                timestamp=reading.timestamp,
                metric_name=reading.metric_name,
                value=reading.value,
                unit=reading.unit,
            )
            for reading in db_readings
        ]
