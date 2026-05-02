from datetime import datetime, timezone

from sqlalchemy import inspect

from libkoiki.models.login_attempt import LoginAttemptModel


def test_created_at_aliases_attempted_at_without_duplicate_column_mapping():
    mapper = inspect(LoginAttemptModel)

    assert "attempted_at" in mapper.attrs
    assert "created_at" in mapper.attrs
    assert len([column for column in mapper.columns if column.name == "attempted_at"]) == 1


def test_created_at_alias_reads_and_writes_attempted_at():
    attempted_at = datetime(2026, 5, 2, tzinfo=timezone.utc)
    updated_at = datetime(2026, 5, 3, tzinfo=timezone.utc)
    attempt = LoginAttemptModel(
        email="user@example.com",
        ip_address="127.0.0.1",
        is_successful=False,
        attempted_at=attempted_at,
    )

    assert attempt.created_at == attempted_at

    attempt.created_at = updated_at

    assert attempt.attempted_at == updated_at
