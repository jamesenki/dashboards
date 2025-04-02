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

    # Check if the water heater with the given ID exists
    if not water_heater:
        # If not, redirect to the water heater list page
        return RedirectResponse(url="/water-heaters", status_code=302)

    return templates.TemplateResponse(
        "water-heater/detail.html",
        {"request": request, "heater_id": heater_id, "now": datetime.now()},
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
