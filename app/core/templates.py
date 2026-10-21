from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.csrf import csrf_input
from app.core.timeutils import format_local

templates = Jinja2Templates(directory="templates")
templates.env.globals["csrf_input"] = csrf_input
templates.env.filters["localtime"] = format_local
# Dados da empresa usados no rodapé e nas páginas legais
templates.env.globals["company"] = {
    "name": settings.COMPANY_NAME,
    "document": settings.COMPANY_DOCUMENT,
    "address": settings.COMPANY_ADDRESS,
    "contact_email": settings.CONTACT_EMAIL,
    "privacy_email": settings.PRIVACY_EMAIL,
    "app_name": settings.APP_NAME,
    "base_url": settings.APP_BASE_URL.rstrip("/"),
    "last_updated": settings.LEGAL_LAST_UPDATED,
}
