"""Tests for the /audits router."""

from unittest.mock import patch, MagicMock

from tests.conftest import FakeQueryBuilder


def _setup_authed_user(fake_supabase):
    """Set up a standard authenticated user with org."""
    fake_supabase.set_table_data(
        "users",
        {"org_id": "org-1", "role": "owner", "email": "test@example.com"},
    )


def test_list_audits_no_auth(client):
    resp = client.get("/audits")
    assert resp.status_code == 401


def test_list_audits_empty(client, fake_supabase, auth_headers):
    _setup_authed_user(fake_supabase)
    fake_supabase.set_table_data("audits", [])

    resp = client.get("/audits", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_audits_returns_data(client, fake_supabase, auth_headers):
    _setup_authed_user(fake_supabase)
    fake_supabase.set_table_data(
        "audits",
        [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "org_id": "00000000-0000-0000-0000-000000000099",
                "url": "https://example.com",
                "status": "complete",
            }
        ],
    )

    resp = client.get("/audits", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["url"] == "https://example.com"


def test_create_audit_queues_task(client, fake_supabase, auth_headers):
    _setup_authed_user(fake_supabase)
    fake_supabase.set_table_data(
        "audits",
        [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "org_id": "00000000-0000-0000-0000-000000000099",
                "created_by": "00000000-0000-0000-0000-000000000123",
                "url": "https://example.com",
                "status": "queued",
            }
        ],
    )

    with patch("app.tasks.audit_tasks.run_audit") as mock_task:
        mock_task.delay = MagicMock()
        resp = client.post(
            "/audits",
            json={"url": "https://example.com"},
            headers=auth_headers,
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "queued"


def test_create_audit_kill_switch(client, fake_supabase, auth_headers):
    """When KILL_AUDIT_QUEUE is set, audit creation should return 503."""
    import os

    _setup_authed_user(fake_supabase)

    os.environ["KILL_AUDIT_QUEUE"] = "true"
    from app.config import get_settings

    get_settings.cache_clear()

    try:
        with patch("sentry_sdk.init"):
            import importlib
            import app.main

            importlib.reload(app.main)
            from fastapi.testclient import TestClient

            kill_client = TestClient(app.main.app)
            resp = kill_client.post(
                "/audits",
                json={"url": "https://example.com"},
                headers=auth_headers,
            )
            assert resp.status_code == 503
    finally:
        os.environ["KILL_AUDIT_QUEUE"] = "false"
        get_settings.cache_clear()


def test_delete_audit_not_found(client, fake_supabase, auth_headers):
    _setup_authed_user(fake_supabase)
    fake_supabase.set_table_data("audits", None)

    resp = client.delete(
        "/audits/00000000-0000-0000-0000-000000000001",
        headers=auth_headers,
    )
    assert resp.status_code == 404
