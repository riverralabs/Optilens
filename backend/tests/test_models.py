"""Tests for Pydantic models — validation logic."""

import pytest
from pydantic import ValidationError

from app.models.audit import AuditCreate, IssueUpdate
from app.models.tracking import EventIngest


def test_audit_create_valid_url():
    audit = AuditCreate(url="https://example.com")
    assert str(audit.url) == "https://example.com/"


def test_audit_create_invalid_url():
    with pytest.raises(ValidationError):
        AuditCreate(url="not-a-url")


def test_issue_update_valid_statuses():
    for status in ("open", "in_progress", "resolved", "dismissed"):
        issue = IssueUpdate(status=status)
        assert issue.status == status


def test_issue_update_invalid_status():
    with pytest.raises(ValueError):
        IssueUpdate(status="deleted")


def test_event_ingest_valid():
    data = EventIngest(
        org_id="00000000-0000-0000-0000-000000000001",
        session_id="sess-1",
        events=[
            {"page_url": "https://example.com", "event_type": "click"},
        ],
    )
    assert len(data.events) == 1


def test_event_ingest_empty_events():
    data = EventIngest(
        org_id="00000000-0000-0000-0000-000000000001",
        session_id="sess-1",
        events=[],
    )
    assert data.events == []
