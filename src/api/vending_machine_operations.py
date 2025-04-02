"""
Vending machine operations API endpoints
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from src.models.vending_machine_operations import (  # New models for Polar Delight Ice Cream Machines
    AssetHealth,
    IceCreamInventoryItem,
    LocationPerformance,
    MaintenanceHistory,
    OperationalStatus,
    OperationsSummary,
    RefillHistory,
    SalesData,
    SalesPeriod,
    ServiceTicket,
    TemperatureTrends,
    UsagePattern,
)
from src.services.service_locator import get_service
from src.services.vending_machine_operations_service import (
    VendingMachineOperationsService,
)


# Service dependency
def get_vending_machine_operations_service():
    """Get ice cream machine operations service instance"""
    from src.services.vending_machine import VendingMachineService
    from src.utils.dummy_data import dummy_data

    # Create the vending machine service first (we're keeping the same service structure)
    vm_service = VendingMachineService(dummy_data)

    # Then create the operations service with the vending machine service
    return VendingMachineOperationsService(vm_service)


# Create router
router = APIRouter(prefix="/ice-cream-machines", tags=["polar-delight-operations"])


@router.get(
    "/fleet/operations",
    response_model=OperationsSummary,
    summary="Get fleet operations summary",
    description="Get the complete operations summary for all Polar Delight ice cream machines",
)
def get_fleet_operations_summary(
    service: VendingMachineOperationsService = Depends(
        get_vending_machine_operations_service
    ),
):
    """Get fleet-wide operations summary for all ice cream machines"""
    try:
        return service.get_fleet_operations_summary()
    except Exception as e:
        # Log the error but don't expose internal details to the frontend
        import logging

        logging.error(f"Error generating fleet operations summary: {str(e)}")

        # Return a generic error with helpful message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred processing fleet operations data. Please try again later.",
        )


@router.get(
    "/{machine_id}/asset-health",
    response_model=AssetHealth,
    summary="Get asset health data",
    description="Get the real-time asset health data for a specific Polar Delight ice cream machine",
)
def get_asset_health(
    machine_id: str = Path(..., description="Ice cream machine ID"),
    service: VendingMachineOperationsService = Depends(
        get_vending_machine_operations_service
    ),
):
    """Get asset health data for a specific ice cream machine"""
    try:
        # Get operational status data to convert to asset health
        operational_status = service.get_operational_status(machine_id)

        # Map operational data to asset health model
        # Calculate a health score based on component statuses
        freezer_ok = (
            float(operational_status.freezer_temperature.get("freezerTemperature", 0))
            < 0
        )
        ram_ok = operational_status.ram_position.get("status", "FAULT") == "OK"
        dispense_ok = operational_status.dispense_pressure.get("status", "OK") == "OK"

        # Get gauge data from operational status
        return AssetHealth(
            asset_id=operational_status.machine_id,
            machine_status=operational_status.machine_status,
            pod_code=operational_status.pod_code,
            cup_detect=operational_status.cup_detect,
            pod_bin_door=operational_status.pod_bin_door,
            customer_door=operational_status.customer_door,
            # Convert gauge data to the required format
            asset_health={
                "value": "85%",
                "status": "OK"
                if (freezer_ok and ram_ok and dispense_ok)
                else "Warning",
            },
            freezer_temperature=operational_status.freezer_temperature,
            dispense_force=operational_status.dispense_pressure,
            cycle_time=operational_status.cycle_time,
            max_ram_load=operational_status.max_ram_load,
            # Location info
            asset_location=operational_status.location,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        import logging

        logging.error(f"Error retrieving asset health for {machine_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred retrieving asset health data. Please try again later.",
        )


@router.get(
    "/{machine_id}/operations",
    response_model=OperationalStatus,
    summary="Get real-time operational data",
    description="Get real-time operational monitoring data for a specific ice cream machine (matches Angular implementation)",
)
def get_operations_summary(
    machine_id: str = Path(..., description="Ice cream machine ID"),
    service: VendingMachineOperationsService = Depends(
        get_vending_machine_operations_service
    ),
):
    """Get real-time operational monitoring data for a specific ice cream machine (matching Angular implementation)"""
    try:
        # This now returns real-time operational data, separate from asset health data
        return service.get_operational_status(machine_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # Log the error but don't expose internal details to the frontend
        import logging

        logging.error(f"Error generating operational data for {machine_id}: {str(e)}")

        # Return a generic error with helpful message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred processing operational data. Please try again later.",
        )


@router.get(
    "/{machine_id}/operations/sales",
    response_model=SalesData,
    summary="Get ice cream sales data",
    description="Get ice cream sales data for a specific period",
)
def get_sales_data(
    machine_id: str = Path(..., description="Ice cream machine ID"),
    period: str = Query(
        "week", description="Sales data period (day, week, month, quarter, year)"
    ),
    service: VendingMachineOperationsService = Depends(
        get_vending_machine_operations_service
    ),
):
    """Get sales data for a Polar Delight ice cream machine"""
    try:
        return service.get_sales_data(machine_id, period)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST
            if "period" in str(e).lower()
            else status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ice cream sales data: {str(e)}",
        )


@router.get(
    "/{machine_id}/operations/maintenance",
    response_model=MaintenanceHistory,
    summary="Get maintenance history",
    description="Get the maintenance history for a Polar Delight ice cream machine",
)
def get_maintenance_history(
    machine_id: str = Path(..., description="Ice cream machine ID"),
    service: VendingMachineOperationsService = Depends(
        get_vending_machine_operations_service
    ),
):
    """Get maintenance history for a Polar Delight ice cream machine"""
    try:
        return service.get_maintenance_history(machine_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get maintenance history: {str(e)}",
        )


@router.get(
    "/{machine_id}/operations/temperature",
    response_model=TemperatureTrends,
    summary="Get freezer temperature trends",
    description="Get freezer temperature trend data for a Polar Delight ice cream machine",
)
def get_temperature_trends(
    machine_id: str = Path(..., description="Ice cream machine ID"),
    service: VendingMachineOperationsService = Depends(
        get_vending_machine_operations_service
    ),
):
    """Get freezer temperature trends for a Polar Delight ice cream machine"""
    try:
        return service.get_temperature_trends(machine_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get freezer temperature trends: {str(e)}",
        )


@router.get(
    "/{machine_id}/operations/refills",
    response_model=RefillHistory,
    summary="Get ice cream pod refill history",
    description="Get the ice cream pod refill history for a Polar Delight ice cream machine",
)
def get_refill_history(
    machine_id: str = Path(..., description="Ice cream machine ID"),
    service: VendingMachineOperationsService = Depends(
        get_vending_machine_operations_service
    ),
):
    """Get ice cream pod refill history for a Polar Delight ice cream machine"""
    try:
        return service.get_refill_history(machine_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ice cream pod refill history: {str(e)}",
        )


@router.get(
    "/{machine_id}/operations/usage",
    response_model=UsagePattern,
    summary="Get ice cream machine usage patterns",
    description="Get usage pattern data for a Polar Delight ice cream machine",
)
def get_usage_patterns(
    machine_id: str = Path(..., description="Ice cream machine ID"),
    service: VendingMachineOperationsService = Depends(
        get_vending_machine_operations_service
    ),
):
    """Get usage patterns for a Polar Delight ice cream machine"""
    try:
        return service.get_usage_patterns(machine_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ice cream machine usage patterns: {str(e)}",
        )
