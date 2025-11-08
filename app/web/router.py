from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from libkoiki.api.dependencies import DBSessionDep, TodoServiceDep

from .dependencies import OptionalWebUser, WebActiveUser
from .templates import templates

router = APIRouter(prefix="/app", tags=["Web"], include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: OptionalWebUser = None,
) -> HTMLResponse:
    """Landing page that exposes login CTA and available tools."""
    context = {
        "request": request,
        "current_user": current_user,
    }
    return templates.TemplateResponse("dashboard/index.html", context)


@router.get("/todo", response_class=HTMLResponse)
async def todo_home(
    request: Request,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
) -> HTMLResponse:
    """Secure ToDo board for authenticated users."""
    todos = await todo_service.get_todos_by_owner(
        owner_id=current_user.id,
        skip=0,
        limit=50,
        db=db,
    )
    context = {
        "request": request,
        "current_user": current_user,
        "todos": todos,
    }
    return templates.TemplateResponse("todo/index.html", context)


@router.get("/todo/rows", response_class=HTMLResponse)
async def todo_rows(
    request: Request,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
) -> HTMLResponse:
    """HTMX endpoint that refreshes the ToDo table rows."""
    todos = await todo_service.get_todos_by_owner(
        owner_id=current_user.id,
        skip=0,
        limit=50,
        db=db,
    )
    context = {
        "request": request,
        "current_user": current_user,
        "todos": todos,
    }
    return templates.TemplateResponse("todo/_rows.html", context)
