"""Tests for the /workspace router."""


def test_get_workspace_no_auth(client):
    resp = client.get("/workspace")
    assert resp.status_code == 401


def test_get_workspace_success(client, fake_supabase, auth_headers):
    fake_supabase.set_table_data("users", {"org_id": "org-1", "role": "owner"})
    fake_supabase.set_table_data(
        "organizations",
        {"id": "org-1", "name": "Test Org", "plan": "pro"},
    )

    resp = client.get("/workspace", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Org"


def test_invite_member_bad_role(client, fake_supabase, auth_headers):
    fake_supabase.set_table_data("users", {"org_id": "org-1", "role": "owner"})

    resp = client.post(
        "/workspace/members/invite",
        json={"email": "new@example.com", "role": "superadmin"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_invite_member_success(client, fake_supabase, auth_headers):
    fake_supabase.set_table_data("users", {"org_id": "org-1", "role": "admin"})

    resp = client.post(
        "/workspace/members/invite",
        json={"email": "new@example.com", "role": "analyst"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "invited"
    assert data["email"] == "new@example.com"


def test_invite_member_viewer_forbidden(client, fake_supabase, auth_headers):
    """Viewers cannot invite members."""
    fake_supabase.set_table_data("users", {"org_id": "org-1", "role": "viewer"})

    resp = client.post(
        "/workspace/members/invite",
        json={"email": "new@example.com", "role": "analyst"},
        headers=auth_headers,
    )
    assert resp.status_code == 403
