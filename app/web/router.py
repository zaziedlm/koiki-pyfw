from typing import Optional, Sequence

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from libkoiki.api.dependencies import DBSessionDep, TodoServiceDep
from libkoiki.core.exceptions import ResourceNotFoundException
from libkoiki.schemas.todo import TodoCreate, TodoUpdate

from .dependencies import (
    OptionalWebUser,
    WebActiveUser,
    issue_csrf_token_for_user,
    verify_web_csrf_token,
)
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
        "csrf_token": issue_csrf_token_for_user(current_user),
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
        "csrf_token": issue_csrf_token_for_user(current_user),
    }
    return templates.TemplateResponse("todo/index.html", context)


@router.get("/todo/rows", response_class=HTMLResponse)
async def todo_rows(
    request: Request,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
) -> HTMLResponse:
    """HTMX endpoint that refreshes the full ToDo table."""
    return await _render_table(
        request,
        current_user,
        todo_service,
        db,
        csrf_token=issue_csrf_token_for_user(current_user),
    )


async def _render_table(
    request: Request,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
    *,
    csrf_token: Optional[str],
    todos: Optional[Sequence] = None,
) -> HTMLResponse:
    if todos is None:
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
        "csrf_token": csrf_token,
    }
    return templates.TemplateResponse("todo/_table.html", context)


async def _render_row(
    request: Request,
    current_user: WebActiveUser,
    todo,
    *,
    csrf_token: Optional[str],
) -> HTMLResponse:
    context = {
        "request": request,
        "current_user": current_user,
        "todo": todo,
        "csrf_token": csrf_token,
    }
    return templates.TemplateResponse("todo/_row.html", context)


@router.post("/todo", response_class=HTMLResponse)
async def create_todo_htmx(
    request: Request,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
    title: str = Form(...),
    description: str = Form(default=""),
    csrf_guard: None = Depends(verify_web_csrf_token),
) -> HTMLResponse:
    """
    Todoを新規作成してテーブル全体を再描画する。

    commitの直後に``db.expire_all()``を実行し、SQLAlchemyのアイデンティティマップを
    クリアしてから``_render_table``で最新の一覧を再取得する。
    """
    todo_in = TodoCreate(title=title, description=description or None)
    try:
        await todo_service.create_todo(todo_in=todo_in, owner_id=current_user.id, db=db)
        await db.commit()
        todos = await todo_service.get_todos_by_owner(
            owner_id=current_user.id,
            skip=0,
            limit=50,
            db=db,
        )
    except Exception:
        await db.rollback()
        raise
    return await _render_table(
        request,
        current_user,
        todo_service,
        db,
        csrf_token=issue_csrf_token_for_user(current_user),
        todos=todos,
    )


@router.get("/todo/{todo_id}/edit", response_class=HTMLResponse)
async def edit_todo_form(
    request: Request,
    todo_id: int,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
    csrf_guard: None = Depends(verify_web_csrf_token),
) -> HTMLResponse:
    try:
        todo = await todo_service.get_todo_by_id(
            todo_id=todo_id, owner_id=current_user.id, db=db
        )
    except ResourceNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )

    context = {
        "request": request,
        "current_user": current_user,
        "todo": todo,
        "csrf_token": issue_csrf_token_for_user(current_user),
    }
    return templates.TemplateResponse("todo/_form_edit.html", context)


@router.put("/todo/{todo_id}", response_class=HTMLResponse)
async def update_todo_htmx(
    request: Request,
    todo_id: int,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
    title: str = Form(...),
    description: str = Form(default=""),
    csrf_guard: None = Depends(verify_web_csrf_token),
) -> HTMLResponse:
    """
    Todoの内容を更新し、該当行のみを再描画する。

    commit後に``db.refresh(updated)``を呼び出し、返却するORMインスタンスを
    必ずコミット済みの最新値にしてからテンプレートに渡す。
    """
    cleaned_title = title.strip()
    if not cleaned_title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title is required"
        )
    todo_in = TodoUpdate(
        title=cleaned_title,
        description=description or None,
    )
    try:
        updated = await todo_service.update_todo(
            todo_id=todo_id,
            todo_in=todo_in,
            owner_id=current_user.id,
            db=db,
        )
        await db.commit()
        await db.refresh(updated)
    except Exception:
        await db.rollback()
        raise
    return await _render_row(
        request,
        current_user,
        updated,
        csrf_token=issue_csrf_token_for_user(current_user),
    )


@router.get("/todo/{todo_id}/view", response_class=HTMLResponse)
async def todo_row_view(
    request: Request,
    todo_id: int,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
) -> HTMLResponse:
    try:
        todo = await todo_service.get_todo_by_id(
            todo_id=todo_id, owner_id=current_user.id, db=db
        )
    except ResourceNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return await _render_row(
        request,
        current_user,
        todo,
        csrf_token=issue_csrf_token_for_user(current_user),
    )


@router.post("/todo/{todo_id}/toggle", response_class=HTMLResponse)
async def toggle_todo(
    request: Request,
    todo_id: int,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
    csrf_guard: None = Depends(verify_web_csrf_token),
) -> HTMLResponse:
    """
    Todoの完了フラグをトグルし、対象行だけを描画し直す。

    commit後に``db.refresh(updated)``を実行して最新値を取得し、HTMXへの部分レスポンス
    が常にコミット済みの状態を反映するようにしている。
    """
    try:
        existing = await todo_service.get_todo_by_id(
            todo_id=todo_id, owner_id=current_user.id, db=db
        )
    except ResourceNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )

    todo_in = TodoUpdate(is_completed=not existing.is_completed)
    try:
        updated = await todo_service.update_todo(
            todo_id=todo_id,
            todo_in=todo_in,
            owner_id=current_user.id,
            db=db,
        )
        await db.commit()
        await db.refresh(updated)
    except Exception:
        await db.rollback()
        raise
    return await _render_row(
        request,
        current_user,
        updated,
        csrf_token=issue_csrf_token_for_user(current_user),
    )


@router.delete("/todo/{todo_id}", response_class=HTMLResponse)
async def delete_todo_htmx(
    request: Request,
    todo_id: int,
    current_user: WebActiveUser,
    todo_service: TodoServiceDep,
    db: DBSessionDep,
    csrf_guard: None = Depends(verify_web_csrf_token),
) -> HTMLResponse:
    """
    Todoを削除し、テーブル全体を再描画する。

    commit後に``db.expire_all()``でアイデンティティマップを無効化し、
    ``_render_table``で再取得する一覧が確実に最新状態になるようにしている。
    """
    try:
        await todo_service.delete_todo(todo_id=todo_id, owner_id=current_user.id, db=db)
        await db.commit()
        todos = await todo_service.get_todos_by_owner(
            owner_id=current_user.id,
            skip=0,
            limit=50,
            db=db,
        )
    except ResourceNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    except Exception:
        await db.rollback()
        raise
    return await _render_table(
        request,
        current_user,
        todo_service,
        db,
        csrf_token=issue_csrf_token_for_user(current_user),
        todos=todos,
    )
