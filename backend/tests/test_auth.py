"""Tests for the /auth router."""


def test_get_me_no_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_get_me_bad_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401


def test_get_me_onboarding_incomplete(client, fake_supabase, auth_headers):
    """User exists in Supabase Auth but has no users row yet."""
    # users table returns no data → onboarding incomplete
    fake_supabase.set_table_data("users", None)

    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarding_complete"] is False
    assert data["org_id"] is None


def test_get_me_onboarding_complete(client, fake_supabase, auth_headers):
    """User has completed onboarding — has a users row + org."""
    fake_supabase.set_table_data(
        "users",
        {"org_id": "org-1", "role": "owner", "email": "test@example.com"},
    )
    fake_supabase.set_table_data(
        "organizations",
        {"id": "org-1", "name": "Test Org", "plan": "pro"},
    )

    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarding_complete"] is True
    assert data["org_id"] == "org-1"
    assert data["organization"]["name"] == "Test Org"
