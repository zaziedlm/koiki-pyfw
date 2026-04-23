import importlib
import inspect
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from libkoiki.schemas.todo import TodoCreate, TodoUpdate
from libkoiki.schemas.user import UserCreate, UserUpdate


@pytest.fixture
def logging_setup(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_ENV", "testing")

    config_module = importlib.import_module("libkoiki.core.config")
    importlib.reload(config_module)

    logging_module = importlib.import_module("libkoiki.core.logging")
    logging_module = importlib.reload(logging_module)
    logging_module.setup_logging()
    return logging_module


@pytest.fixture
def base_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.repositories.base")
    return importlib.reload(module)


@pytest.fixture
def user_service_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.services.user_service")
    return importlib.reload(module)


@pytest.fixture
def todo_service_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.services.todo_service")
    return importlib.reload(module)


@pytest.fixture
def users_endpoint_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.api.v1.endpoints.users")
    return importlib.reload(module)


@pytest.fixture
def todos_endpoint_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.api.v1.endpoints.todos")
    return importlib.reload(module)


@pytest.fixture
def user_sso_repository_module(logging_setup):
    del logging_setup
    module = importlib.import_module("app.repositories.user_sso_repository")
    return importlib.reload(module)


@pytest.fixture
def event_handlers_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.events.handlers")
    return importlib.reload(module)


@pytest.fixture
def event_publisher_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.events.publisher")
    return importlib.reload(module)


@pytest.fixture
def email_utils_module(logging_setup):
    del logging_setup
    module = importlib.import_module("libkoiki.utils.email")
    return importlib.reload(module)


@pytest.fixture
def task_email_module(logging_setup, monkeypatch):
    del logging_setup
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND", raising=False)
    sys.modules.pop("libkoiki.tasks.celery_app", None)
    sys.modules.pop("libkoiki.tasks.email", None)
    sys.modules["libkoiki.tasks.celery_app"] = SimpleNamespace(celery_app=None)
    module = importlib.import_module("libkoiki.tasks.email")
    return importlib.reload(module)


class TestRepositoryInputLogging:
    @pytest.mark.asyncio
    async def test_base_repository_create_and_update_log_field_names_only(
        self,
        base_module,
    ):
        class DummyModel:
            __name__ = "DummyModel"

        repository = base_module.BaseRepository(DummyModel)
        repository.set_session(
            SimpleNamespace(
                add=MagicMock(),
                flush=AsyncMock(),
                refresh=AsyncMock(),
            )
        )
        base_module.logger = MagicMock()

        obj = SimpleNamespace(
            id=1,
            email="user@example.com",
            hashed_password="hash-value",
            _sa_instance_state=object(),
        )

        await repository.create(obj)
        create_kwargs = base_module.logger.debug.call_args.kwargs
        assert create_kwargs["field_names"] == ["email", "id"]
        assert "data" not in create_kwargs

        update_target = SimpleNamespace(id=1, email="user@example.com", full_name=None)
        await repository.update(
            update_target,
            {
                "email": "updated@example.com",
                "password": "secret-password",
                "full_name": "Updated User",
            },
        )

        update_kwargs = base_module.logger.debug.call_args.kwargs
        assert update_kwargs["update_fields"] == ["email", "full_name"]
        assert "update_data" not in update_kwargs


class TestServiceInputLogging:
    @pytest.mark.asyncio
    async def test_user_service_logs_field_names_without_raw_input_values(
        self,
        user_service_module,
    ):
        repository = MagicMock()
        repository.set_session = MagicMock()
        repository.get = AsyncMock(
            return_value=SimpleNamespace(
                id=10,
                email="current@example.com",
                is_active=True,
            )
        )
        repository.get_by_email = AsyncMock(return_value=None)
        repository.update = AsyncMock(
            return_value=SimpleNamespace(id=10, email="updated@example.com")
        )

        service = user_service_module.UserService(repository=repository)
        user_service_module.logger = MagicMock()
        db = MagicMock()
        db.execute = AsyncMock(
            return_value=SimpleNamespace(
                scalar_one_or_none=MagicMock(
                    return_value=SimpleNamespace(id=10, email="updated@example.com")
                )
            )
        )

        endpoint = inspect.unwrap(user_service_module.UserService.update_user)
        await endpoint(
            service,
            user_id=10,
            user_in=UserUpdate(email="updated@example.com", password="NewPass123!"),
            db=db,
        )

        info_kwargs = [call.kwargs for call in user_service_module.logger.info.call_args_list]
        debug_kwargs = [call.kwargs for call in user_service_module.logger.debug.call_args_list]
        warning_kwargs = [call.kwargs for call in user_service_module.logger.warning.call_args_list]

        assert any(kwargs.get("update_fields") == ["email"] for kwargs in info_kwargs)
        assert all("data" not in kwargs for kwargs in info_kwargs)
        assert all("new_email" not in kwargs for kwargs in debug_kwargs + warning_kwargs)

    @pytest.mark.asyncio
    async def test_todo_service_logs_field_names_without_raw_payload(
        self,
        todo_service_module,
    ):
        repository = MagicMock()
        repository.set_session = MagicMock()
        repository.get_by_id_and_owner = AsyncMock(
            return_value=SimpleNamespace(id=7, owner_id=1)
        )
        repository.update = AsyncMock(
            return_value=SimpleNamespace(id=7, owner_id=1)
        )

        service = todo_service_module.TodoService(repository=repository)
        todo_service_module.logger = MagicMock()

        endpoint = inspect.unwrap(todo_service_module.TodoService.update_todo)
        await endpoint(
            service,
            todo_id=7,
            todo_in=TodoUpdate(title="Secret title", description="Secret body"),
            owner_id=1,
            db=MagicMock(),
        )

        info_kwargs = [call.kwargs for call in todo_service_module.logger.info.call_args_list]
        assert any(kwargs.get("update_fields") == ["description", "title"] for kwargs in info_kwargs)
        assert all("data" not in kwargs for kwargs in info_kwargs)


class TestEndpointInputLogging:
    @pytest.mark.asyncio
    async def test_users_endpoints_log_field_names_instead_of_raw_values(
        self,
        users_endpoint_module,
    ):
        users_endpoint_module.logger = MagicMock()
        user_service = MagicMock()
        user_service.create_user = AsyncMock(
            return_value=SimpleNamespace(id=1, email="user@example.com")
        )
        user_service.update_user = AsyncMock(
            return_value=SimpleNamespace(id=1)
        )
        user_service.get_user_with_roles = AsyncMock(return_value=SimpleNamespace(id=1))

        create_endpoint = inspect.unwrap(users_endpoint_module.create_user)
        await create_endpoint(
            request=SimpleNamespace(),
            user_in=UserCreate(
                username="tester",
                email="user@example.com",
                password="Secret123!",
                full_name="Test User",
            ),
            user_service=user_service,
            db=MagicMock(),
        )

        create_kwargs = users_endpoint_module.logger.info.call_args_list[0].kwargs
        assert create_kwargs["provided_fields"] == ["email", "full_name", "username"]
        assert "email" not in create_kwargs

        update_endpoint = inspect.unwrap(users_endpoint_module.update_user_me)
        await update_endpoint(
            request=SimpleNamespace(),
            user_in=UserUpdate(email="updated@example.com", password="Secret123!"),
            current_user=SimpleNamespace(id=1),
            user_service=user_service,
            db=MagicMock(),
        )

        update_kwargs = users_endpoint_module.logger.info.call_args_list[2].kwargs
        assert update_kwargs["update_fields"] == ["email"]
        assert "data" not in update_kwargs

    @pytest.mark.asyncio
    async def test_todos_endpoints_log_field_names_instead_of_raw_values(
        self,
        todos_endpoint_module,
    ):
        todos_endpoint_module.logger = MagicMock()
        todo_service = MagicMock()
        todo_service.create_todo = AsyncMock(return_value=SimpleNamespace(id=10))
        todo_service.update_todo = AsyncMock(return_value=SimpleNamespace(id=10))

        create_endpoint = inspect.unwrap(todos_endpoint_module.create_todo)
        await create_endpoint(
            request=SimpleNamespace(),
            todo_in=TodoCreate(title="Private title", description="Private body"),
            current_user=SimpleNamespace(id=3),
            todo_service=todo_service,
            db=MagicMock(),
        )

        create_kwargs = todos_endpoint_module.logger.info.call_args_list[0].kwargs
        assert create_kwargs["provided_fields"] == ["description", "title"]
        assert "title" not in create_kwargs

        update_endpoint = inspect.unwrap(todos_endpoint_module.update_todo)
        await update_endpoint(
            request=SimpleNamespace(),
            todo_id=10,
            todo_in=TodoUpdate(title="Private title", description="Private body"),
            current_user=SimpleNamespace(id=3),
            todo_service=todo_service,
            db=MagicMock(),
        )

        update_kwargs = todos_endpoint_module.logger.info.call_args_list[2].kwargs
        assert update_kwargs["update_fields"] == ["description", "title"]
        assert "data" not in update_kwargs


class TestRemainingInputLogging:
    @pytest.mark.skip(reason="Requires app module not available in libkoiki test context; should live in app test suite")
    @pytest.mark.asyncio
    async def test_user_sso_repository_does_not_log_raw_subject_or_email(
        self,
        user_sso_repository_module,
    ):
        repository = user_sso_repository_module.UserSSORepository()
        repository.get_by_user_id = AsyncMock(return_value=[])
        repository.create = AsyncMock(return_value=SimpleNamespace(id=99, user_id=1))
        user_sso_repository_module.logger = MagicMock()

        await repository.create_sso_link(
            user_id=1,
            sso_subject_id="subject-123",
            sso_provider="oidc",
            sso_email="user@example.com",
            sso_display_name="Test User",
        )

        info_kwargs = [call.kwargs for call in user_sso_repository_module.logger.info.call_args_list]
        assert any(kwargs.get("provided_fields") == ["sso_display_name", "sso_email", "sso_subject_id"] for kwargs in info_kwargs)
        assert all("sso_subject_id" not in kwargs or isinstance(kwargs["sso_subject_id"], int) for kwargs in info_kwargs)
        assert all("sso_email" not in kwargs for kwargs in info_kwargs)

    @pytest.mark.asyncio
    async def test_event_handler_logs_payload_fields_instead_of_raw_payload(
        self,
        event_handlers_module,
    ):
        event_handlers_module.logger = MagicMock()
        handler = event_handlers_module.EventHandler(redis_client=MagicMock())

        async def sample_handler(data):
            return data

        await handler._run_handler(
            sample_handler,
            {"user_id": 1, "email": "user@example.com", "access_token": "secret"},
            "user.created",
        )

        info_kwargs = event_handlers_module.logger.info.call_args.kwargs
        assert info_kwargs["payload_fields"] == ["email", "user_id"]
        assert "data" not in info_kwargs

    @pytest.mark.asyncio
    async def test_user_created_handler_does_not_log_raw_email(
        self,
        event_handlers_module,
    ):
        event_handlers_module.logger = MagicMock()
        fake_task = SimpleNamespace(delay=MagicMock())
        fake_module = SimpleNamespace(send_welcome_email_task=fake_task)

        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(sys.modules, "libkoiki.tasks.email", fake_module)
            await event_handlers_module.user_created_handler(
                {"user_id": 1, "email": "user@example.com"}
            )

        info_kwargs = [call.kwargs for call in event_handlers_module.logger.info.call_args_list]
        assert any(kwargs.get("user_id") == 1 for kwargs in info_kwargs)
        assert all("email" not in kwargs for kwargs in info_kwargs)

    @pytest.mark.asyncio
    async def test_event_publisher_logs_payload_fields_instead_of_event_data(
        self,
        event_publisher_module,
    ):
        event_publisher_module.logger = MagicMock()
        redis_client = SimpleNamespace(publish=AsyncMock(return_value=1))
        publisher = event_publisher_module.EventPublisher(redis_client)

        await publisher.publish(
            "user.created",
            {"user_id": 1, "email": "user@example.com", "access_token": "secret"},
        )

        info_kwargs = event_publisher_module.logger.info.call_args.kwargs
        assert info_kwargs["payload_fields"] == ["email", "user_id"]
        assert "data" not in info_kwargs

    def test_send_email_logs_context_fields_only(
        self,
        email_utils_module,
    ):
        email_utils_module.logger = MagicMock()

        email_utils_module.send_email(
            to_email="user@example.com",
            subject="Welcome user@example.com",
            template_name="welcome_email.html",
            context={"user_email": "user@example.com", "reset_token": "secret"},
        )

        first_info = email_utils_module.logger.info.call_args_list[0].kwargs
        second_info = email_utils_module.logger.info.call_args_list[1].kwargs
        assert first_info["context_fields"] == ["user_email"]
        assert "to_email" not in first_info
        assert "subject" not in first_info
        assert second_info["template_name"] == "welcome_email.html"
        assert "to_email" not in second_info

    def test_dummy_email_task_does_not_log_raw_email(
        self,
        task_email_module,
    ):
        task_email_module.logger = MagicMock()

        task_email_module.send_welcome_email_task(1, "user@example.com")

        warning_kwargs = task_email_module.logger.warning.call_args.kwargs
        assert "email" not in warning_kwargs
