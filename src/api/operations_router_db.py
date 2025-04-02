"""
API routes for operations dashboard data using database-backed services.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.db.adapters.operations_cache import OperationsDashboardCache
from src.db.adapters.redis_cache import RedisCache, get_redis_cache
from src.db.repository import DeviceRepository
from src.services.vending_machine_operations_service_db import (
    VendingMachineOperationsServiceDB,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_operations_service(
    device_repo: DeviceRepository = Depends(),
    redis_cache: RedisCache = Depends(get_redis_cache),
) -> VendingMachineOperationsServiceDB:
    """Dependency for getting operations service with database backing."""
    ops_cache = OperationsDashboardCache(redis_cache)
    return VendingMachineOperationsServiceDB(device_repo, ops_cache, redis_cache)


@router.get("/vending-machines/{vm_id}/operations/realtime")
async def get_vm_realtime_operations(
    vm_id: str,
    service: VendingMachineOperationsServiceDB = Depends(get_operations_service),
):
    """
    Get real-time operations data for a vending machine.
    This endpoint uses PostgreSQL for persistence and Redis for caching.
    """
    try:
        return await service.get_vm_operations(vm_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting operations data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ice-cream-machines/{machine_id}/operations")
async def get_ice_cream_operations(
    machine_id: str,
    service: VendingMachineOperationsServiceDB = Depends(get_operations_service),
):
    """
    Get real-time operations data for an ice cream machine.
    This uses the same database as vending machines but formats the data
    to match the original Angular implementation.
    """
    try:
        return await service.get_ice_cream_operations(machine_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting ice cream operations data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ice-cream-machines/fleet/operations")
async def get_fleet_operations(
    service: VendingMachineOperationsServiceDB = Depends(get_operations_service),
):
    """
    Get fleet-wide operations overview for all machines.
    """
    try:
        return await service.get_fleet_operations()
    except Exception as e:
        logger.error(f"Error getting fleet operations data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/vending-machines/{vm_id}/operations/update")
async def update_vm_operations(
    vm_id: str,
    update_data: Dict,
    service: VendingMachineOperationsServiceDB = Depends(get_operations_service),
):
    """
    Update operational data for a vending machine.
    This will invalidate related cache entries.
    """
    try:
        await service.update_vm_operations(vm_id, update_data)
        return {"status": "success", "message": f"Updated operations data for {vm_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating operations data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
