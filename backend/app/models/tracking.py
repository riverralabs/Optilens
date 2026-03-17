"""Pydantic models for event tracking and heatmap data."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class EventData(BaseModel):
    page_url: str
    event_type: str  # click, scroll, move
    x: Optional[float] = None
    y: Optional[float] = None
    viewport_w: Optional[int] = None
    viewport_h: Optional[int] = None


class EventIngest(BaseModel):
    org_id: UUID
    audit_id: Optional[UUID] = None
    session_id: str
    events: list[EventData]


class HeatmapPoint(BaseModel):
    x: float
    y: float
    value: int
    event_type: str


class HeatmapResponse(BaseModel):
    audit_id: str
    points: list[HeatmapPoint]
