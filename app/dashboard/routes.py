from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
import requests

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")

@router.get("/")
def dashboard(request: Request):
    ip = request.client.host

    try:
        geo = requests.get(f"https://ipapi.co/{ip}/json/").json()
    except:
        geo = {}

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "ip": ip,
            "city": geo.get("city", "Unknown"),
            "country": geo.get("country_name", "Unknown"),
            "org": geo.get("org", "Unknown"),
            "datetime": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "vpn_status": "OFF"
        }
    )
