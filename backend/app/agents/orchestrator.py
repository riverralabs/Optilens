"""Orchestrator agent — initializes state, dispatches agents, synthesizes results.

This is the entry point for the LangGraph audit pipeline.
Full implementation in Step 1.6.
"""

from __future__ import annotations

import logging
from typing import Callable, TypedDict

logger = logging.getLogger("optilens.agents.orchestrator")


class AuditState(TypedDict):
    """Shared state passed between all agents in the pipeline."""

    # Input
    audit_id: str
    org_id: str
    url: str
    pages: list[str]
    ga4_connected: bool
    gsc_connected: bool
    github_connected: bool

    # Context (set by Site Intelligence agent)
    site_type: str       # ecommerce|saas|landing_page|corporate|webapp
    framework: list[str]  # ['AIDA', 'Baymard', etc.]
    primary_kpi: str

    # Raw data
    screenshots: dict[str, str]  # page_url -> base64 screenshot
    dom_content: dict[str, str]  # page_url -> HTML

    # Agent outputs
    ux_issues: list[dict]
    copy_issues: list[dict]
    performance_data: dict
    seo_issues: list[dict]

    # Final
    cro_score: int
    revenue_leak_monthly: float
    revenue_leak_confidence: str  # High|Medium|Estimated
    issues: list[dict]
    agent_outputs: dict


# Type alias for the progress callback used by Celery tasks
ProgressCallback = Callable[[str, str, str, int], None]


def run_audit_pipeline(
    audit_id: str,
    org_id: str,
    url: str,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    """Run the full LangGraph agent pipeline for an audit.

    Pipeline order:
    1. orchestrator_init -> 2. site_intelligence ->
    3. ux_vision, copy_content, data_performance (parallel) ->
    4. orchestrator_synthesis -> 5. report_agent

    Args:
        audit_id: The audit record ID.
        org_id: The organization ID (for data isolation).
        url: The target URL to audit.
        progress_callback: Optional callback(audit_id, agent, status, progress)
            used by the Celery task to publish real-time progress.

    Full implementation in Step 1.6.
    """
    logger.info("Starting audit pipeline: audit_id=%s url=%s", audit_id, url)

    # Placeholder — Step 1.6 will implement the full LangGraph StateGraph
    raise NotImplementedError(
        "Audit pipeline not yet implemented. Build in Step 1.6."
    )
