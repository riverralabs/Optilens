"""GitHub routes — PR details, approve, reject.

Phase 4 implementation.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger("optilens.github")


@router.get("/audits/{audit_id}/pr")
async def get_pr(audit_id: UUID) -> dict:
    """Get PR details and diff for an audit."""
    return {"status": "not_available", "message": "GitHub integration available in Phase 4"}


@router.post("/audits/{audit_id}/pr/approve")
async def approve_pr(audit_id: UUID) -> dict:
    """Approve a PR via GitHub API."""
    return {"status": "not_available", "message": "GitHub integration available in Phase 4"}


@router.post("/audits/{audit_id}/pr/reject")
async def reject_pr(audit_id: UUID) -> dict:
    """Reject and close a PR."""
    return {"status": "not_available", "message": "GitHub integration available in Phase 4"}
