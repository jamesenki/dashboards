"""
Vending machine real-time operations API endpoints
"""
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.models.vending_machine_realtime_operations import VendingMachineOperationsData
from src.services.vending_machine_realtime_operations_service import (
    VendingMachineRealtimeOperationsService,
)


# Service dependency
def get_vending_machine_realtime_operations_service():
    """Get vending machine real-time operations service instance"""
    from src.services.vending_machine import VendingMachineService
    from src.utils.dummy_data import dummy_data

    # Create the vending machine service first
    vm_service = VendingMachineService(dummy_data)

    # Then create the operations service with the vending machine service
    return VendingMachineRealtimeOperationsService(vm_service)


# Create router
router = APIRouter(
    prefix="/vending-machines-realtime", tags=["vending-machine-operations"]
)


@router.get(
    "/{machine_id}/operations/realtime",
    response_model=VendingMachineOperationsData,
    summary="Get real-time operations data",
    description="Get the real-time operations data for a vending machine",
)
def get_realtime_operations_data(
    machine_id: str = Path(..., description="Vending machine ID"),
    service: VendingMachineRealtimeOperationsService = Depends(
        get_vending_machine_realtime_operations_service
    ),
):
    """Get real-time operations data for a vending machine"""
    try:
        # The service will use the vending_machine_service's fallback mechanism
        # to generate mock data for non-existent machines
        return service.get_operations_data(machine_id)
    except Exception as e:
        # Log the error but don't expose internal details to the frontend
        import logging

        logging.error(
            f"Error generating realtime operations data for {machine_id}: {str(e)}"
        )

        # Return a generic error with helpful message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred processing real-time operations data. Please try again later.",
        )
