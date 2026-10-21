from fastapi.templating import Jinja2Templates

from app.core.csrf import csrf_input
from app.core.timeutils import format_local

templates = Jinja2Templates(directory="templates")
templates.env.globals["csrf_input"] = csrf_input
templates.env.filters["localtime"] = format_local
