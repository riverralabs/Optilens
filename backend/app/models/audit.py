"""Pydantic models for audit-related data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class AuditCreate(BaseModel):
    url: HttpUrl


class AuditResponse(BaseModel):
    id: UUID
    org_id: UUID
    created_by: Optional[UUID] = None
    url: str
    site_type: Optional[str] = None
    framework_applied: Optional[list[str]] = None
    status: str
    cro_score: Optional[int] = None
    previous_score: Optional[int] = None
    revenue_leak_monthly: Optional[float] = None
    revenue_leak_confidence: Optional[str] = None
    pages_audited: Optional[list] = None
    agent_outputs: Optional[dict] = None
    audit_duration_seconds: Optional[int] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class IssueResponse(BaseModel):
    id: UUID
    audit_id: UUID
    org_id: UUID
    agent: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    title: str
    description: Optional[str] = None
    recommendation: Optional[str] = None
    affected_element: Optional[str] = None
    screenshot_url: Optional[str] = None
    ice_score: Optional[float] = None
    impact_score: Optional[int] = None
    confidence_score: Optional[int] = None
    effort_score: Optional[int] = None
    revenue_impact_monthly: Optional[float] = None
    ab_variants: Optional[list] = None
    status: str
    created_at: Optional[datetime] = None


class IssueUpdate(BaseModel):
    status: str

    def model_post_init(self, __context: object) -> None:
        valid_statuses = {"open", "in_progress", "resolved", "dismissed"}
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of: {valid_statuses}")
