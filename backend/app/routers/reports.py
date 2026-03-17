"""Report routes — get report URLs, regenerate reports."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.db.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger("optilens.reports")


@router.get("/audits/{audit_id}/report")
async def get_report(audit_id: UUID, request: Request) -> dict:
    """Get report URLs (PDF, Excel, screenshots ZIP) for an audit."""
    supabase = get_supabase_client()
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    token = auth_header.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)
    user_id = user_response.user.id

    user_row = supabase.table("users").select("org_id").eq("id", user_id).single().execute()
    if not user_row.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = user_row.data["org_id"]

    result = (
        supabase.table("reports")
        .select("*")
        .eq("audit_id", str(audit_id))
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")

    report = result.data

    # Generate signed URLs for each asset
    urls: dict[str, str | None] = {}
    for field, bucket in [
        ("pdf_url", "reports"),
        ("excel_url", "exports"),
        ("screenshots_zip_url", "exports"),
    ]:
        path = report.get(field)
        if path:
            signed = supabase.storage.from_(bucket).create_signed_url(path, 3600)
            urls[field.replace("_url", "")] = signed.get("signedURL")
        else:
            urls[field.replace("_url", "")] = None

    return {
        "id": report["id"],
        "audit_id": report["audit_id"],
        "pdf": urls.get("pdf"),
        "excel": urls.get("excel"),
        "screenshots_zip": urls.get("screenshots_zip"),
        "generated_at": report["generated_at"],
        "expires_at": report["expires_at"],
    }


@router.post("/audits/{audit_id}/report/regen")
async def regenerate_report(audit_id: UUID, request: Request) -> dict:
    """Re-generate the report for an audit."""
    supabase = get_supabase_client()
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")

    token = auth_header.replace("Bearer ", "")
    user_response = supabase.auth.get_user(token)
    user_id = user_response.user.id

    user_row = supabase.table("users").select("org_id").eq("id", user_id).single().execute()
    if not user_row.data:
        raise HTTPException(status_code=403, detail="User not found")
    org_id = user_row.data["org_id"]

    # Verify audit exists and is complete
    audit = (
        supabase.table("audits")
        .select("status")
        .eq("id", str(audit_id))
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not audit.data:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.data["status"] != "complete":
        raise HTTPException(status_code=400, detail="Audit must be complete to regenerate report")

    from app.tasks.audit_tasks import generate_report_task
    generate_report_task.delay(str(audit_id))

    logger.info("Report regeneration queued for audit %s", audit_id)
    return {"status": "queued", "message": "Report regeneration started"}
