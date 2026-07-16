from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from libkoiki.core.exceptions import ConflictException, ResourceNotFoundException
from libkoiki.db.base import Base
from libkoiki.models.todo import TodoModel
from libkoiki.repositories.todo_repository import TodoRepository
from libkoiki.schemas.todo import TodoUpdate
from libkoiki.services.todo_service import TodoService


@pytest.fixture
def service() -> TodoService:
    return TodoService(repository=TodoRepository())


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an in-memory AsyncSession backed by SQLite for transactional tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        if session.in_transaction():
            await session.rollback()

    await engine.dispose()


async def _create_todo(session: AsyncSession, *, owner_id: int = 1) -> TodoModel:
    todo = TodoModel(title="Original", description=None, is_completed=False, owner_id=owner_id, version=1)
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    return todo


@pytest.mark.asyncio
async def test_update_todo_with_correct_version_succeeds_and_increments_version(
    service: TodoService, async_session: AsyncSession
):
    todo = await _create_todo(async_session)

    updated = await service.update_todo(
        todo_id=todo.id,
        todo_in=TodoUpdate(title="Updated title", version=1),
        owner_id=1,
        db=async_session,
    )

    assert updated.title == "Updated title"
    assert updated.version == 2


@pytest.mark.asyncio
async def test_update_todo_with_stale_version_raises_conflict(
    service: TodoService, async_session: AsyncSession
):
    todo = await _create_todo(async_session)

    await service.update_todo(
        todo_id=todo.id,
        todo_in=TodoUpdate(title="First update", version=1),
        owner_id=1,
        db=async_session,
    )

    with pytest.raises(ConflictException):
        await service.update_todo(
            todo_id=todo.id,
            todo_in=TodoUpdate(title="Second update (stale)", version=1),
            owner_id=1,
            db=async_session,
        )


@pytest.mark.asyncio
async def test_update_missing_todo_raises_not_found(
    service: TodoService, async_session: AsyncSession
):
    with pytest.raises(ResourceNotFoundException):
        await service.update_todo(
            todo_id=999,
            todo_in=TodoUpdate(title="Does not exist", version=1),
            owner_id=1,
            db=async_session,
        )
