"""
Web routes for the frontend templates
"""
from pathlib import Path as FilePath

from fastapi import APIRouter, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Set up templates
project_root = FilePath(__file__).parent.parent.parent
templates_dir = project_root / "frontend/templates"
templates = Jinja2Templates(directory=templates_dir)

# Create router
router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Render the index page"""
    # For now we'll keep the water heater list as the home page
    # but this could be updated to a dashboard with multiple device types
    return templates.TemplateResponse("water-heater/list.html", {"request": request})


@router.get("/water-heaters", response_class=HTMLResponse)
async def get_water_heater_list(request: Request):
    """Render the water heater list page"""
    return templates.TemplateResponse("water-heater/list.html", {"request": request})


@router.get("/diagnostic", response_class=HTMLResponse)
async def get_diagnostic_page(request: Request):
    """Render the API diagnostic page"""
    return templates.TemplateResponse("diagnostic.html", {"request": request})


@router.get("/water-heaters/debug", response_class=HTMLResponse)
async def get_water_heater_debug_page(request: Request):
    """Render the water heater debug page"""
    return templates.TemplateResponse("water-heater/debug.html", {"request": request})


@router.get("/water-heaters/standalone", response_class=HTMLResponse)
async def get_water_heater_standalone_page(request: Request):
    """Render the standalone water heater page that doesn't rely on WaterHeaterList class"""
    return templates.TemplateResponse(
        "water-heater/standalone.html", {"request": request}
    )


@router.get("/water-heaters/new", response_class=HTMLResponse)
async def get_new_water_heater_form(request: Request):
    """Render the new water heater form"""
    return templates.TemplateResponse(
        "water-heater/form.html", {"request": request, "heater_id": None}
    )


@router.get("/water-heaters/{heater_id}", response_class=HTMLResponse)
async def get_water_heater_detail(request: Request, heater_id: str = Path(...)):
    """Render the water heater detail page"""
    from datetime import datetime

    from fastapi.responses import RedirectResponse

    from src.services.configurable_water_heater_service import (
        ConfigurableWaterHeaterService,
    )

    # Use the ConfigurableWaterHeaterService to check if the water heater exists
    service = ConfigurableWaterHeaterService()
    water_heater = await service.get_water_heater(heater_id)

    # Special handling for AquaTherm water heaters
    # This ensures AquaTherm water heaters can be viewed even if not yet in the database
    if not water_heater:
        # Check if this is an AquaTherm water heater by ID pattern
        if heater_id.startswith("aqua-wh-"):
            import logging

            try:
                logging.info(
                    f"AquaTherm water heater ID detected: {heater_id}. Creating on-demand."
                )

                # Get water heater data from the manufacturer-agnostic implementation
                from src.utils.dummy_data import dummy_data

                # Find matching heater data from the dummy data
                matching_heater = None
                for heater_id_key, heater in dummy_data.water_heaters.items():
                    if heater_id_key == heater_id:
                        matching_heater = {
                            "id": heater.id,
                            "name": heater.name,
                            "manufacturer": heater.manufacturer,
                            "model": heater.model,
                            "status": heater.status.value,
                        }
                        break

                if matching_heater:
                    # If found in dummy data, create it in the database
                    from datetime import datetime

                    from src.models.device import DeviceStatus, DeviceType
                    from src.models.water_heater import (
                        WaterHeater,
                        WaterHeaterMode,
                        WaterHeaterStatus,
                        WaterHeaterType,
                    )

                    # Handle the readings separately - they may not match the model structure
                    readings = matching_heater.pop("readings", [])

                    # Create heater object with basic properties
                    water_heater = WaterHeater(
                        id=matching_heater["id"],
                        name=matching_heater["name"],
                        type=DeviceType.WATER_HEATER,
                        manufacturer=matching_heater["manufacturer"],
                        model=matching_heater["model"],
                        status=DeviceStatus(matching_heater["status"]),
                        heater_status=WaterHeaterStatus(
                            matching_heater["heater_status"]
                        ),
                        mode=WaterHeaterMode(matching_heater["mode"]),
                        current_temperature=matching_heater["current_temperature"],
                        target_temperature=matching_heater["target_temperature"],
                        min_temperature=matching_heater["min_temperature"],
                        max_temperature=matching_heater["max_temperature"],
                        last_seen=datetime.now(),
                        last_updated=datetime.now(),
                        heater_type=WaterHeaterType.RESIDENTIAL,
                        readings=[],  # Initialize with empty readings
                        location="AquaTherm Test Location",  # Add required location field
                    )

                    # Add to database
                    created_heater = await service.create_water_heater(water_heater)
                    logging.info(
                        f"Created AquaTherm water heater {heater_id} in database"
                    )
                    water_heater = created_heater
                else:
                    # If not found in AquaTherm data either, redirect to list page
                    logging.warning(
                        f"AquaTherm water heater {heater_id} not found in AquaTherm data"
                    )
                    return RedirectResponse(url="/water-heaters", status_code=302)
            except Exception as e:
                # Log any errors during AquaTherm creation but continue to show the detail page
                logging.error(f"Error creating AquaTherm water heater: {str(e)}")
                # Return a simple template response instead of an error
                return templates.TemplateResponse(
                    "water-heater/detail.html",
                    {
                        "request": request,
                        "heater_id": heater_id,
                        "now": datetime.now(),
                        "error": str(e),
                        "water_heater": {
                            "id": heater_id
                        },  # Pass minimal water_heater object
                    },
                )
        else:
            # For non-AquaTherm water heaters, redirect to the list page if not found
            return RedirectResponse(url="/water-heaters", status_code=302)

    return templates.TemplateResponse(
        "water-heater/detail.html",
        {
            "request": request,
            "heater_id": heater_id,
            "now": datetime.now(),
            "water_heater": water_heater,  # Pass the water_heater object to the template
        },
    )


@router.get("/water-heaters/{heater_id}/edit", response_class=HTMLResponse)
async def get_edit_water_heater_form(request: Request, heater_id: str = Path(...)):
    """Render the edit water heater form"""
    return templates.TemplateResponse(
        "water-heater/form.html", {"request": request, "heater_id": heater_id}
    )


@router.get("/vending-machines", response_class=HTMLResponse)
async def get_vending_machine_list(request: Request):
    """Render the vending machine list page"""
    return templates.TemplateResponse("vending-machine/list.html", {"request": request})


@router.get("/vending-machines/new", response_class=HTMLResponse)
async def get_new_vending_machine_form(request: Request):
    """Render the new vending machine form"""
    return templates.TemplateResponse(
        "vending-machine/form.html", {"request": request, "machine_id": None}
    )


@router.get("/vending-machines/detail", response_class=HTMLResponse)
async def get_vending_machine_dashboard(request: Request):
    """Render the vending machine dashboard page"""
    from datetime import datetime

    return templates.TemplateResponse(
        "vending-machine/detail.html", {"request": request, "now": datetime.now()}
    )


@router.get("/vending-machines/{machine_id}", response_class=HTMLResponse)
async def get_vending_machine_detail(request: Request, machine_id: str = Path(...)):
    """Render the vending machine detail page"""
    from datetime import datetime

    return templates.TemplateResponse(
        "vending-machine/detail.html",
        {"request": request, "machine_id": machine_id, "now": datetime.now()},
    )


@router.get("/vending-machines/{machine_id}/edit", response_class=HTMLResponse)
async def get_edit_vending_machine_form(request: Request, machine_id: str = Path(...)):
    """Render the edit vending machine form"""
    return templates.TemplateResponse(
        "vending-machine/form.html", {"request": request, "machine_id": machine_id}
    )


# Add monitoring dashboard routes
@router.get("/monitoring", response_class=HTMLResponse)
async def get_monitoring_dashboard(request: Request):
    """Render the model monitoring dashboard page"""
    return templates.TemplateResponse(
        "model-monitoring/dashboard.html", {"request": request}
    )


@router.get("/monitoring/alerts", response_class=HTMLResponse)
async def get_monitoring_alerts(request: Request):
    """Render the model monitoring alerts page"""
    return templates.TemplateResponse(
        "model-monitoring/alerts.html", {"request": request}
    )


@router.get("/model-monitoring", response_class=HTMLResponse)
async def get_model_monitoring_dashboard(request: Request):
    """Render the model monitoring dashboard"""
    return templates.TemplateResponse(
        "model-monitoring/dashboard.html", {"request": request}
    )


@router.get("/model-monitoring/models", response_class=HTMLResponse)
async def get_model_monitoring_models(request: Request):
    """Render the model monitoring models tab"""
    return templates.TemplateResponse(
        "model-monitoring/models.html", {"request": request}
    )


@router.get("/model-monitoring/alerts", response_class=HTMLResponse)
async def get_model_monitoring_alerts(request: Request):
    """Render the model monitoring alerts tab"""
    return templates.TemplateResponse(
        "model-monitoring/alerts.html", {"request": request}
    )


@router.get("/model-monitoring/reports", response_class=HTMLResponse)
async def get_model_monitoring_reports(request: Request):
    """Render the model monitoring reports tab"""
    return templates.TemplateResponse(
        "model-monitoring/reports.html", {"request": request}
    )
