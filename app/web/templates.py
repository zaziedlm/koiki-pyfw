from pathlib import Path

from fastapi.templating import Jinja2Templates

from libkoiki.core.config import settings

TEMPLATE_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.globals["settings"] = settings
