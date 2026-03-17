# Optilens API Reference

See `Claude.md` for the full API specification.

Base URL: `http://localhost:8000` (dev) / `https://api.optilens.ai` (prod)

## Authentication

All endpoints require a Supabase JWT token in the `Authorization: Bearer <token>` header.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /audits | Create + queue new audit |
| GET | /audits | List audits (org-scoped) |
| GET | /audits/{id} | Get audit + agent outputs |
| GET | /audits/{id}/status | SSE streaming status |
| POST | /audits/{id}/rerun | Re-queue audit |
| DELETE | /audits/{id} | Delete audit + assets |
| GET | /audits/{id}/issues | Issues for audit |
| PATCH | /issues/{id} | Update issue status |
| GET | /audits/{id}/report | Report URLs |
| POST | /audits/{id}/report/regen | Regenerate report |
| GET | /integrations | List integrations |
| GET | /workspace | Org details |
| POST | /track | Ingest rrweb events |
| GET | /heatmap/{audit_id} | Heatmap data |
