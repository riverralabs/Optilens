"""Shared fixtures for all backend tests.

Provides a FastAPI test client with mocked Supabase and auth dependencies,
so tests run without any external services.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set required env vars BEFORE any app imports
os.environ.update(
    {
        "ANTHROPIC_API_KEY": "test-key",
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_KEY": "test-service-key",
        "SUPABASE_ANON_KEY": "test-anon-key",
        "GOOGLE_CLIENT_ID": "test-google-id",
        "GOOGLE_CLIENT_SECRET": "test-google-secret",
        "GITHUB_APP_ID": "12345",
        "GITHUB_CLIENT_ID": "test-gh-id",
        "GITHUB_CLIENT_SECRET": "test-gh-secret",
        "GITHUB_PRIVATE_KEY": "test-gh-key-placeholder-32chars!!",
        "REDIS_URL": "redis://localhost:6379",
        "LANGFUSE_PUBLIC_KEY": "test-lf-pub",
        "LANGFUSE_SECRET_KEY": "test-lf-secret",
        "LANGFUSE_HOST": "https://cloud.langfuse.com",
        "SENTRY_DSN": "https://test@sentry.io/123",
        "ENCRYPTION_KEY": "a]bCdEfGhIjKlMnOpQrStUvWxYz123456",
        "APP_ENV": "testing",
        "CORS_ORIGINS": "http://localhost:5173",
    }
)


@dataclass
class FakeUser:
    id: str = "user-123"
    email: str = "test@example.com"


class FakeUserResponse:
    def __init__(self, user: FakeUser | None = None):
        self.user = user or FakeUser()


class FakeQueryBuilder:
    """Chainable mock that simulates Supabase query builder."""

    def __init__(self, data: list[dict] | dict | None = None):
        self._data = data
        self._single = False

    def select(self, *args: Any, **kwargs: Any) -> FakeQueryBuilder:
        return self

    def insert(self, data: Any) -> FakeQueryBuilder:
        # Keep pre-set data if available (simulates server-side defaults like id)
        if self._data:
            return self
        if isinstance(data, dict):
            self._data = [data]
        elif isinstance(data, list):
            self._data = data
        return self

    def update(self, data: Any) -> FakeQueryBuilder:
        if self._data and isinstance(self._data, list):
            self._data = [{**self._data[0], **data}]
        return self

    def delete(self) -> FakeQueryBuilder:
        return self

    def eq(self, *args: Any) -> FakeQueryBuilder:
        return self

    def order(self, *args: Any, **kwargs: Any) -> FakeQueryBuilder:
        return self

    def single(self) -> FakeQueryBuilder:
        self._single = True
        return self

    def maybeSingle(self) -> FakeQueryBuilder:
        self._single = True
        return self

    def execute(self) -> Any:
        @dataclass
        class Result:
            data: Any

        if self._single and isinstance(self._data, list):
            return Result(data=self._data[0] if self._data else None)
        return Result(data=self._data)


class FakeSupabaseAuth:
    def get_user(self, token: str) -> FakeUserResponse:
        if token == "bad-token":
            raise Exception("Invalid token")
        return FakeUserResponse()


class FakeSupabase:
    """Minimal mock of the Supabase client."""

    def __init__(self) -> None:
        self.auth = FakeSupabaseAuth()
        self._tables: dict[str, list[dict]] = {}

    def set_table_data(self, table: str, data: list[dict] | dict | None) -> None:
        if data is None:
            self._tables[table] = []
        elif isinstance(data, dict):
            self._tables[table] = [data]
        else:
            self._tables[table] = data

    def table(self, name: str) -> FakeQueryBuilder:
        data = self._tables.get(name, [])
        return FakeQueryBuilder(data)


@pytest.fixture()
def fake_supabase() -> FakeSupabase:
    return FakeSupabase()


@pytest.fixture()
def client(fake_supabase: FakeSupabase) -> TestClient:
    """Create a test client with mocked Supabase and Sentry."""
    from app.config import get_settings

    # Clear the lru_cache so test env vars take effect
    get_settings.cache_clear()

    # Patch get_supabase_client everywhere it's imported
    patches = [
        patch("app.db.supabase.get_supabase_client", return_value=fake_supabase),
        patch("app.auth.get_supabase_client", return_value=fake_supabase),
        patch("app.routers.auth.get_supabase_client", return_value=fake_supabase),
        patch("app.routers.audits.get_supabase_client", return_value=fake_supabase),
        patch("app.routers.workspace.get_supabase_client", return_value=fake_supabase),
        patch("app.routers.issues.get_supabase_client", return_value=fake_supabase),
        patch("app.routers.track.get_supabase_client", return_value=fake_supabase),
        patch("sentry_sdk.init"),
    ]

    for p in patches:
        p.start()

    try:
        import importlib

        import app.main

        importlib.reload(app.main)
        yield TestClient(app.main.app)
    finally:
        for p in patches:
            p.stop()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Bearer token header for authenticated requests."""
    return {"Authorization": "Bearer test-valid-token"}
