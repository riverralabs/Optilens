"""Tests for the /track router."""


def test_ingest_events(client, fake_supabase):
    fake_supabase.set_table_data("events", [])

    resp = client.post(
        "/track",
        json={
            "org_id": "00000000-0000-0000-0000-000000000001",
            "session_id": "sess-abc",
            "events": [
                {
                    "page_url": "https://example.com",
                    "event_type": "click",
                    "x": 100.0,
                    "y": 200.0,
                    "viewport_w": 1920,
                    "viewport_h": 1080,
                }
            ],
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "accepted"
    assert data["count"] == 1


def test_ingest_multiple_events(client, fake_supabase):
    fake_supabase.set_table_data("events", [])

    resp = client.post(
        "/track",
        json={
            "org_id": "00000000-0000-0000-0000-000000000001",
            "session_id": "sess-abc",
            "events": [
                {"page_url": "https://example.com", "event_type": "click", "x": 10, "y": 20},
                {"page_url": "https://example.com", "event_type": "scroll", "x": 0, "y": 500},
                {"page_url": "https://example.com/about", "event_type": "move", "x": 300, "y": 400},
            ],
        },
    )
    assert resp.status_code == 202
    assert resp.json()["count"] == 3


def test_heatmap_no_auth(client):
    resp = client.get("/heatmap/00000000-0000-0000-0000-000000000001")
    assert resp.status_code == 401


def test_heatmap_returns_points(client, fake_supabase, auth_headers):
    fake_supabase.set_table_data(
        "events",
        [
            {"x": 100, "y": 200, "event_type": "click", "page_url": "https://example.com"},
            {"x": 150, "y": 250, "event_type": "click", "page_url": "https://example.com"},
        ],
    )

    resp = client.get(
        "/heatmap/00000000-0000-0000-0000-000000000001",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["audit_id"] == "00000000-0000-0000-0000-000000000001"
    assert len(data["points"]) == 2
