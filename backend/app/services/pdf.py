"""WeasyPrint PDF generation service.

Generates branded audit reports as PDF files. Structure follows the spec:
cover page, executive summary, CRO score breakdown, critical issues,
UX analysis, copy analysis, performance/SEO, revenue impact, prioritized
backlog, and appendix.

White-label ready: if org has white_label_config with logo/colors, those
are applied instead of Optilens branding.
"""

from __future__ import annotations

import base64
import io
import logging
from datetime import datetime, timezone

from weasyprint import HTML

from app.db.supabase import get_supabase_client

logger = logging.getLogger("optilens.services.pdf")


def generate_audit_pdf(audit: dict) -> str:
    """Generate a branded PDF report for a completed audit.

    Args:
        audit: Full audit dict from Supabase (with agent_outputs populated).

    Returns:
        The storage path of the uploaded PDF in the 'reports' bucket.
    """
    audit_id = audit["id"]
    org_id = audit["org_id"]

    # Fetch org details for branding
    supabase = get_supabase_client()
    org_result = supabase.table("organizations").select("name, white_label_config").eq("id", org_id).single().execute()
    org = org_result.data or {}

    # Fetch issues for this audit
    issues_result = supabase.table("issues").select("*").eq("audit_id", audit_id).order("ice_score", desc=True).execute()
    issues = issues_result.data or []

    # Build HTML
    html_content = _build_report_html(audit, org, issues)

    # Render PDF
    pdf_bytes = HTML(string=html_content).write_pdf()

    # Upload to Supabase Storage
    file_name = f"{audit_id}/report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"

    supabase.storage.from_("reports").upload(
        file_name,
        pdf_bytes,
        {"content-type": "application/pdf"},
    )

    logger.info("PDF report generated and uploaded: %s (%d bytes)", file_name, len(pdf_bytes))
    return file_name


def get_signed_pdf_url(storage_path: str, expires_in: int = 7776000) -> str | None:
    """Generate a signed URL for a PDF report (default 90 days)."""
    try:
        supabase = get_supabase_client()
        result = supabase.storage.from_("reports").create_signed_url(storage_path, expires_in)
        return result.get("signedURL")
    except Exception as exc:
        logger.error("PDF signed URL failed: %s", exc)
        return None


def _build_report_html(audit: dict, org: dict, issues: list[dict]) -> str:
    """Build the complete HTML for the PDF report."""
    agent_outputs = audit.get("agent_outputs") or {}
    cro_score = audit.get("cro_score") or 0
    url = audit.get("url", "")
    site_type = audit.get("site_type", "unknown")
    frameworks = audit.get("framework_applied") or []
    revenue_leak = audit.get("revenue_leak_monthly") or 0
    confidence = audit.get("revenue_leak_confidence", "Estimated")

    # White-label config
    wl = org.get("white_label_config") or {}
    brand_name = wl.get("name", "Optilens")
    primary_color = wl.get("primary_color", "#1C1C1C")
    accent_color = wl.get("accent_color", "#FF5401")
    org_name = org.get("name", "")

    # Score band
    score_color = _score_color(cro_score)
    score_band = _score_band(cro_score)

    # Separate issues by type
    critical_issues = [i for i in issues if i.get("severity") == "critical"]
    high_issues = [i for i in issues if i.get("severity") == "high"]
    medium_issues = [i for i in issues if i.get("severity") == "medium"]
    low_issues = [i for i in issues if i.get("severity") == "low"]

    # Score breakdown
    breakdown = agent_outputs.get("score_breakdown", {})

    # Revenue info
    revenue_info = agent_outputs.get("revenue_leak", {})

    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
        font-family: 'Inter', sans-serif;
        font-size: 11pt;
        color: {primary_color};
        line-height: 1.5;
    }}

    h1, h2, h3, h4 {{ font-family: 'Space Grotesk', sans-serif; }}

    .page {{ page-break-after: always; padding: 40px; }}
    .page:last-child {{ page-break-after: avoid; }}

    /* Cover page */
    .cover {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        text-align: center;
        background: {primary_color};
        color: white;
        padding: 60px;
    }}
    .cover h1 {{ font-size: 36pt; margin-bottom: 8px; }}
    .cover .url {{ font-size: 14pt; color: rgba(255,255,255,0.7); margin-bottom: 40px; }}
    .cover .score-circle {{
        width: 160px; height: 160px;
        border-radius: 50%;
        border: 6px solid {accent_color};
        display: flex; align-items: center; justify-content: center;
        margin: 20px auto;
    }}
    .cover .score-value {{ font-size: 48pt; font-weight: 700; color: {accent_color}; }}
    .cover .score-label {{ font-size: 12pt; color: rgba(255,255,255,0.6); margin-top: 8px; }}
    .cover .date {{ font-size: 10pt; color: rgba(255,255,255,0.5); margin-top: 40px; }}
    .cover .brand {{ font-size: 10pt; color: rgba(255,255,255,0.4); margin-top: 10px; }}

    /* Section headers */
    .section-header {{
        font-size: 18pt;
        font-weight: 700;
        color: {primary_color};
        border-bottom: 3px solid {accent_color};
        padding-bottom: 8px;
        margin-bottom: 20px;
        margin-top: 30px;
    }}

    /* Score breakdown bar */
    .score-bar {{
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }}
    .score-bar .label {{
        width: 180px;
        font-size: 10pt;
        font-weight: 500;
    }}
    .score-bar .bar-bg {{
        flex: 1;
        height: 20px;
        background: #F0F0F0;
        border-radius: 4px;
        overflow: hidden;
    }}
    .score-bar .bar-fill {{
        height: 100%;
        border-radius: 4px;
    }}
    .score-bar .value {{
        width: 40px;
        text-align: right;
        font-size: 10pt;
        font-weight: 600;
        margin-left: 10px;
    }}

    /* Issue cards */
    .issue-card {{
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        page-break-inside: avoid;
    }}
    .issue-card .issue-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }}
    .issue-card .issue-title {{
        font-weight: 600;
        font-size: 11pt;
    }}
    .severity-badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 9pt;
        font-weight: 600;
        color: white;
    }}
    .severity-critical {{ background: #FF4D6A; }}
    .severity-high {{ background: #FF5401; }}
    .severity-medium {{ background: #F59E0B; }}
    .severity-low {{ background: #4F8EFF; }}
    .issue-desc {{ font-size: 10pt; color: #4A4A4A; margin-bottom: 8px; }}
    .issue-rec {{
        font-size: 10pt;
        color: {primary_color};
        background: #F6F6F6;
        padding: 8px 12px;
        border-radius: 4px;
        border-left: 3px solid {accent_color};
    }}
    .issue-meta {{
        font-size: 9pt;
        color: #888888;
        margin-top: 8px;
    }}

    /* Revenue card */
    .revenue-card {{
        background: #F6F6F6;
        border-radius: 10px;
        padding: 24px;
        text-align: center;
        margin: 20px 0;
    }}
    .revenue-value {{
        font-size: 32pt;
        font-weight: 700;
        color: {accent_color};
    }}
    .revenue-label {{
        font-size: 10pt;
        color: #888888;
        margin-top: 4px;
    }}
    .confidence-badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 9pt;
        background: #F0F0F0;
        color: #4A4A4A;
        margin-top: 8px;
    }}

    /* Table */
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 10pt;
        margin: 16px 0;
    }}
    th {{
        background: {primary_color};
        color: white;
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
    }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #E0E0E0; }}
    tr:nth-child(even) {{ background: #FAFAFA; }}

    /* Footer */
    .footer {{
        font-size: 8pt;
        color: #888888;
        text-align: center;
        margin-top: 40px;
        padding-top: 16px;
        border-top: 1px solid #E0E0E0;
    }}
</style>
</head>
<body>

<!-- COVER PAGE -->
<div class="cover page">
    <h1>{brand_name}</h1>
    <div class="url">{url}</div>
    <div class="score-circle">
        <span class="score-value">{cro_score}</span>
    </div>
    <div class="score-label">CRO Score — {score_band}</div>
    <div class="date">{date_str}</div>
    <div class="brand">{'Prepared for ' + org_name if org_name else ''}</div>
</div>

<!-- EXECUTIVE SUMMARY -->
<div class="page">
    <h2 class="section-header">Executive Summary</h2>
    <p>{_generate_executive_summary(audit, issues)}</p>

    <div class="revenue-card">
        <div class="revenue-value">${revenue_leak:,.0f}</div>
        <div class="revenue-label">Estimated Monthly Revenue Leak</div>
        <div class="confidence-badge">{confidence} — {revenue_info.get('assumptions', {{}}).get('label', 'Benchmark estimate')}</div>
    </div>

    <h2 class="section-header">CRO Score Breakdown</h2>
    {_render_score_bars(breakdown, accent_color)}

    <p style="font-size: 9pt; color: #888; margin-top: 12px;">
        Site type: {site_type} | Frameworks: {', '.join(frameworks) if frameworks else 'N/A'} |
        Issues found: {len(issues)} | Pages audited: {len((audit.get('pages_audited') or []))}
    </p>
</div>

<!-- CRITICAL ISSUES -->
<div class="page">
    <h2 class="section-header">Critical Issues ({len(critical_issues)})</h2>
    {_render_issues(critical_issues[:5]) if critical_issues else '<p style="color: #22D3A0;">No critical issues found.</p>'}

    <h2 class="section-header">High Priority Issues ({len(high_issues)})</h2>
    {_render_issues(high_issues[:5]) if high_issues else '<p style="color: #22D3A0;">No high priority issues found.</p>'}
</div>

<!-- UX & COPY ANALYSIS -->
<div class="page">
    <h2 class="section-header">UX & Visual Analysis</h2>
    {_render_issues([i for i in issues if i.get('agent') == 'ux'][:10])}

    <h2 class="section-header">Copy & Content Analysis</h2>
    {_render_issues([i for i in issues if i.get('agent') == 'copy'][:10])}
</div>

<!-- PERFORMANCE & SEO -->
<div class="page">
    <h2 class="section-header">Performance & SEO</h2>
    {_render_seo_checklist(agent_outputs.get('data_performance', {{}}).get('seo_checklist', {{}}))}
    {_render_issues([i for i in issues if i.get('agent') in ('seo', 'performance')][:10])}
</div>

<!-- PRIORITIZED BACKLOG -->
<div class="page">
    <h2 class="section-header">Prioritized Backlog (ICE Score)</h2>
    <table>
        <tr><th>#</th><th>Issue</th><th>Severity</th><th>Agent</th><th>ICE</th></tr>
        {_render_backlog_rows(issues)}
    </table>
</div>

<!-- APPENDIX -->
<div class="page">
    <h2 class="section-header">Appendix — Methodology</h2>
    <p style="font-size: 10pt; color: #4A4A4A;">
        This audit was conducted using Optilens AI-powered CRO analysis.
        The CRO score is calculated as a weighted composite:
        UX & Friction (25%), Copy & Persuasion (20%), Performance & CWV (20%),
        SEO (15%), Conversion Psychology (10%), Accessibility (10%).
    </p>
    <p style="font-size: 10pt; color: #4A4A4A; margin-top: 12px;">
        Issues are prioritized using the ICE framework:
        ICE = (Impact x Confidence) / Effort. Higher scores indicate
        higher-impact, higher-confidence issues that are easier to fix.
    </p>
    <p style="font-size: 10pt; color: #4A4A4A; margin-top: 12px;">
        Revenue estimates labeled as "Estimated" use industry benchmarks.
        Connect Google Analytics 4 for real revenue data.
    </p>
    <div class="footer">
        Generated by {brand_name} | {date_str} | optilens.ai
    </div>
</div>

</body>
</html>"""


def _score_color(score: int) -> str:
    """Get the color hex for a CRO score band."""
    if score >= 80:
        return "#22D3A0"
    elif score >= 60:
        return "#F59E0B"
    elif score >= 40:
        return "#FF5401"
    return "#FF4D6A"


def _score_band(score: int) -> str:
    """Get the label for a CRO score band."""
    if score >= 80:
        return "Optimized"
    elif score >= 60:
        return "Needs Work"
    elif score >= 40:
        return "High Risk"
    return "Critical"


def _generate_executive_summary(audit: dict, issues: list[dict]) -> str:
    """Generate a concise executive summary paragraph."""
    score = audit.get("cro_score", 0)
    url = audit.get("url", "")
    site_type = audit.get("site_type", "website")
    band = _score_band(score)

    critical_count = len([i for i in issues if i.get("severity") == "critical"])
    high_count = len([i for i in issues if i.get("severity") == "high"])
    total = len(issues)

    summary = (
        f"The CRO audit of {url} (classified as {site_type}) resulted in a score of "
        f"{score}/100, placing it in the '{band}' band. "
        f"A total of {total} issue{'s' if total != 1 else ''} {'were' if total != 1 else 'was'} identified, "
        f"including {critical_count} critical and {high_count} high-priority items. "
    )

    if critical_count > 0:
        top_issue = next((i for i in issues if i.get("severity") == "critical"), None)
        if top_issue:
            summary += f"The most critical finding is: \"{top_issue.get('title', 'N/A')}\". "

    summary += "See the sections below for detailed findings and actionable recommendations."

    return summary


def _render_score_bars(breakdown: dict, accent: str) -> str:
    """Render the CRO score breakdown as horizontal bars."""
    labels = {
        "ux_friction": "UX & Friction (25%)",
        "copy_persuasion": "Copy & Persuasion (20%)",
        "performance_cwv": "Performance & CWV (20%)",
        "seo": "SEO (15%)",
        "conversion_psychology": "Conversion Psychology (10%)",
        "accessibility": "Accessibility (10%)",
    }

    bars = ""
    for key, label in labels.items():
        value = breakdown.get(key, 50)
        color = _score_color(value)
        bars += f"""
        <div class="score-bar">
            <div class="label">{label}</div>
            <div class="bar-bg"><div class="bar-fill" style="width:{value}%; background:{color};"></div></div>
            <div class="value">{value}</div>
        </div>"""
    return bars


def _render_issues(issues: list[dict]) -> str:
    """Render a list of issue cards."""
    if not issues:
        return "<p style='color: #888;'>No issues in this category.</p>"

    html = ""
    for issue in issues:
        severity = issue.get("severity", "medium")
        ab_html = ""
        if issue.get("ab_variants"):
            ab_html = "<div style='margin-top: 8px; font-size: 9pt;'><strong>A/B Variants:</strong><br>"
            for variant in issue["ab_variants"]:
                ab_html += f"<em>{variant.get('variant', 'A')}:</em> {variant.get('text', '')}<br>"
            ab_html += "</div>"

        html += f"""
        <div class="issue-card">
            <div class="issue-header">
                <span class="issue-title">{issue.get('title', 'Untitled')}</span>
                <span class="severity-badge severity-{severity}">{severity.upper()}</span>
            </div>
            <div class="issue-desc">{issue.get('description', '')}</div>
            <div class="issue-rec"><strong>Recommendation:</strong> {issue.get('recommendation', 'N/A')}</div>
            {ab_html}
            <div class="issue-meta">
                Agent: {issue.get('agent', 'N/A')} |
                ICE Score: {issue.get('ice_score', 'N/A')} |
                Impact: {issue.get('impact_score', '-')}/10
            </div>
        </div>"""
    return html


def _render_seo_checklist(checklist: dict) -> str:
    """Render the SEO checklist as a simple table."""
    if not checklist:
        return ""

    labels = {
        "title_tag": "Title Tag",
        "meta_description": "Meta Description",
        "h1_present": "H1 Present",
        "h1_single": "Single H1",
        "schema_markup": "Schema Markup",
        "viewport_meta": "Viewport Meta",
        "canonical_url": "Canonical URL",
        "og_tags": "Open Graph Tags",
        "image_alt_tags": "Image Alt Tags",
        "robots_meta": "Robots Meta",
    }

    rows = ""
    for key, label in labels.items():
        value = checklist.get(key)
        if value is None:
            continue
        icon = "&#10003;" if value else "&#10007;"
        color = "#22D3A0" if value else "#FF4D6A"
        rows += f"<tr><td>{label}</td><td style='color:{color}; font-weight:bold;'>{icon}</td></tr>"

    if not rows:
        return ""

    return f"""
    <table style="width: 50%; margin-bottom: 20px;">
        <tr><th>Check</th><th>Status</th></tr>
        {rows}
    </table>"""


def _render_backlog_rows(issues: list[dict]) -> str:
    """Render the prioritized backlog table rows."""
    rows = ""
    for i, issue in enumerate(issues[:25], 1):
        severity = issue.get("severity", "medium")
        rows += f"""
        <tr>
            <td>{i}</td>
            <td>{issue.get('title', 'Untitled')}</td>
            <td><span class="severity-badge severity-{severity}" style="font-size:8pt;">{severity}</span></td>
            <td>{issue.get('agent', 'N/A')}</td>
            <td>{issue.get('ice_score', '-')}</td>
        </tr>"""
    return rows
