"""
Web routes for the frontend templates
"""
from fastapi import APIRouter, Request, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path as FilePath

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
    return templates.TemplateResponse("water-heater/form.html", {
        "request": request,
        "heater_id": None
    })

@router.get("/water-heaters/{heater_id}", response_class=HTMLResponse)
async def get_water_heater_detail(request: Request, heater_id: str = Path(...)):
    """Render the water heater detail page"""
    return templates.TemplateResponse("water-heater/detail.html", {
        "request": request,
        "heater_id": heater_id
    })

@router.get("/water-heaters/{heater_id}/edit", response_class=HTMLResponse)
async def get_edit_water_heater_form(request: Request, heater_id: str = Path(...)):
    """Render the edit water heater form"""
    return templates.TemplateResponse("water-heater/form.html", {
        "request": request,
        "heater_id": heater_id
    })

@router.get("/vending-machines", response_class=HTMLResponse)
async def get_vending_machine_list(request: Request):
    """Render the vending machine list page"""
    return templates.TemplateResponse("vending-machine/list.html", {"request": request})

@router.get("/vending-machines/new", response_class=HTMLResponse)
async def get_new_vending_machine_form(request: Request):
    """Render the new vending machine form"""
    return templates.TemplateResponse("vending-machine/form.html", {
        "request": request,
        "machine_id": None
    })

@router.get("/vending-machines/detail", response_class=HTMLResponse)
async def get_vending_machine_dashboard(request: Request):
    """Render the vending machine dashboard page"""
    from datetime import datetime
    return templates.TemplateResponse("vending-machine/detail.html", {
        "request": request,
        "now": datetime.now()
    })

@router.get("/vending-machines/{machine_id}", response_class=HTMLResponse)
async def get_vending_machine_detail(request: Request, machine_id: str = Path(...)):
    """Render the vending machine detail page"""
    from datetime import datetime
    return templates.TemplateResponse("vending-machine/detail.html", {
        "request": request,
        "machine_id": machine_id,
        "now": datetime.now()
    })

@router.get("/vending-machines/{machine_id}/edit", response_class=HTMLResponse)
async def get_edit_vending_machine_form(request: Request, machine_id: str = Path(...)):
    """Render the edit vending machine form"""
    return templates.TemplateResponse("vending-machine/form.html", {
        "request": request,
        "machine_id": machine_id
    })
