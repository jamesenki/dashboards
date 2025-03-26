from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.db.repository import DeviceRepository
from src.models.device import Device, DeviceStatus, DeviceType
from src.models.device_reading import DeviceReading

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=List[Device])
async def list_devices(
    type: Optional[DeviceType] = Query(None, description="Filter by device type"),
    status: Optional[DeviceStatus] = Query(None, description="Filter by device status"),
    repo: DeviceRepository = Depends(),
):
    """List all devices with optional filtering."""
    return await repo.get_devices(type_filter=type, status_filter=status)


@router.post("/", response_model=Device, status_code=201)
async def add_device(
    device: Device,
    repo: DeviceRepository = Depends(),
):
    """Create a new device."""
    # Set last_seen to now if device is online
    if device.status == DeviceStatus.ONLINE:
        device.last_seen = datetime.now()
    
    return await repo.create_device(device)


@router.get("/{device_id}", response_model=Device)
async def get_device_by_id(
    device_id: str,
    repo: DeviceRepository = Depends(),
):
    """Get a device by ID."""
    device = await repo.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=Device)
async def update_device_by_id(
    device_id: str,
    device_data: dict,
    repo: DeviceRepository = Depends(),
):
    """Update a device."""
    # Update last_seen if status is being changed to online
    if "status" in device_data and device_data["status"] == DeviceStatus.ONLINE:
        device_data["last_seen"] = datetime.now()
    
    device = await repo.update_device(device_id, device_data)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.delete("/{device_id}", status_code=204)
async def delete_device_by_id(
    device_id: str,
    repo: DeviceRepository = Depends(),
):
    """Delete a device."""
    success = await repo.delete_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return None


@router.post("/{device_id}/readings", response_model=Device)
async def add_reading(
    device_id: str,
    reading: DeviceReading,
    repo: DeviceRepository = Depends(),
):
    """Add a reading to a device."""
    device = await repo.add_device_reading(device_id, reading)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/{device_id}/readings", response_model=List[DeviceReading])
async def get_device_readings(
    device_id: str,
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    limit: int = Query(100, description="Maximum number of readings to return"),
    offset: int = Query(0, description="Number of readings to skip"),
    repo: DeviceRepository = Depends(),
):
    """Get readings for a device with pagination and filtering."""
    # First verify the device exists
    device = await repo.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return await repo.get_device_readings(
        device_id=device_id,
        metric_name=metric,
        limit=limit,
        offset=offset,
    )
