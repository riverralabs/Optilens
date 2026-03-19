"""Orchestrator agent — initializes state, dispatches agents, synthesizes results.

Builds a LangGraph StateGraph that runs the audit pipeline:
1. orchestrator_init -> 2. site_intelligence ->
3. ux_vision, copy_content, data_performance (parallel) ->
4. orchestrator_synthesis
"""

from __future__ import annotations

import logging
import signal
import time
from typing import Annotated, Callable, TypedDict

from langgraph.graph import END, StateGraph

# Per-agent timeout in seconds — prevents one hanging agent from blocking the pipeline
AGENT_TIMEOUT_SECONDS = 90

logger = logging.getLogger("optilens.agents.orchestrator")


class AuditState(TypedDict, total=False):
    """Shared state passed between all agents in the pipeline."""

    # Input
    audit_id: str
    org_id: str
    url: str
    pages: list[str]
    ga4_connected: bool
    gsc_connected: bool
    github_connected: bool

    # Progress callback (set by Celery task, not serialized)
    progress_callback: Callable | None

    # Context (set by Site Intelligence agent)
    site_type: str       # ecommerce|saas|landing_page|corporate|webapp
    framework: list[str]  # ['AIDA', 'Baymard', etc.]
    primary_kpi: str

    # Raw data (set by crawler in orchestrator_init)
    screenshots: dict[str, str]  # page_url -> base64 screenshot
    mobile_screenshots: dict[str, str]
    dom_content: dict[str, str]  # page_url -> HTML
    page_metadata: dict[str, dict]

    # Agent outputs
    ux_issues: list[dict]
    copy_issues: list[dict]
    performance_data: dict
    seo_issues: list[dict]

    # Site intelligence details
    site_intelligence_output: dict

    # UX details
    ux_score: int
    mobile_score: int
    accessibility_score: int

    # Copy details
    persuasion_score: int
    readability_score: int
    emotional_trigger_map: dict

    # Revenue
    revenue_leak_monthly: float
    revenue_leak_confidence: str  # High|Medium|Estimated
    revenue_leak_assumptions: dict

    # Final
    cro_score: int
    issues: list[dict]
    agent_outputs: dict


# Type alias for the progress callback
ProgressCallback = Callable[[str, str, str, int], None]


# --- CRO Score weights ---
CRO_WEIGHTS = {
    "ux_friction": 0.25,
    "copy_persuasion": 0.20,
    "performance_cwv": 0.20,
    "seo": 0.15,
    "conversion_psychology": 0.10,
    "accessibility": 0.10,
}


def _notify(state: AuditState, agent: str, status: str, progress: int) -> None:
    """Call the progress callback if available."""
    cb = state.get("progress_callback")
    if cb:
        try:
            cb(state["audit_id"], agent, status, progress)
        except Exception:
            pass


class _AgentTimeoutError(Exception):
    """Raised when an agent exceeds its time budget."""


def _run_with_timeout(fn, args=(), kwargs=None, timeout: int = AGENT_TIMEOUT_SECONDS):
    """Run a function with a timeout. Returns result or raises _AgentTimeoutError."""
    import threading

    result = [None]
    exc = [None]

    def target():
        try:
            result[0] = fn(*args, **(kwargs or {}))
        except Exception as e:
            exc[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise _AgentTimeoutError(f"{fn.__name__} timed out after {timeout}s")
    if exc[0]:
        raise exc[0]
    return result[0]


def _persist_agent_output(state: AuditState, agent_name: str, output: dict) -> None:
    """Persist an individual agent's output to Supabase after it completes."""
    try:
        from app.db.supabase import get_supabase_client

        supabase = get_supabase_client()
        audit_id = state["audit_id"]

        # Merge into existing agent_outputs
        current = supabase.table("audits").select("agent_outputs").eq("id", audit_id).single().execute()
        existing_outputs = (current.data or {}).get("agent_outputs") or {}
        existing_outputs[agent_name] = output

        supabase.table("audits").update({
            "agent_outputs": existing_outputs,
        }).eq("id", audit_id).execute()

    except Exception as exc:
        logger.warning("Failed to persist agent output for %s: %s", agent_name, exc)


# ═══════════════════════════════════════
# LangGraph node functions
# ═══════════════════════════════════════

def orchestrator_init(state: AuditState) -> dict:
    """Initialize audit: crawl the target URL, populate state with raw data."""
    from app.services.crawler import crawl_pages

    audit_id = state["audit_id"]
    url = state["url"]

    logger.info("Orchestrator init: crawling %s", url)
    _notify(state, "crawler", "running", 5)

    try:
        crawl_result = _run_with_timeout(crawl_pages, args=(url, state.get("pages")), timeout=120)
    except (_AgentTimeoutError, Exception) as exc:
        logger.error("Crawler failed/timed out for %s: %s", url, exc)
        _notify(state, "crawler", "complete", 10)
        # Return empty result so pipeline can continue with DOM-less analysis
        return {
            "screenshots": {},
            "mobile_screenshots": {},
            "dom_content": {},
            "page_metadata": {},
        }

    _notify(state, "crawler", "complete", 10)

    return {
        "screenshots": crawl_result.screenshots,
        "mobile_screenshots": crawl_result.mobile_screenshots,
        "dom_content": crawl_result.dom_content,
        "page_metadata": crawl_result.page_metadata,
    }


def site_intelligence_node(state: AuditState) -> dict:
    """Run Site Intelligence agent to classify site type and select framework."""
    from app.agents.site_intelligence import run_site_intelligence

    _notify(state, "site_intelligence", "running", 15)

    try:
        result = _run_with_timeout(run_site_intelligence, args=(state,))
    except (_AgentTimeoutError, Exception) as exc:
        logger.error("Site intelligence failed: %s", exc)
        result = {
            "site_type": "landing_page",
            "framework": ["AIDA"],
            "primary_kpi": "conversion_rate",
            "confidence": 0.3,
            "reasoning": f"Fallback — agent failed: {exc}",
        }

    _persist_agent_output(state, "site_intelligence", result)
    _notify(state, "site_intelligence", "complete", 25)

    return {
        "site_type": result["site_type"],
        "framework": result["framework"],
        "primary_kpi": result.get("primary_kpi", "conversion_rate"),
        "site_intelligence_output": result,
    }


def ux_vision_node(state: AuditState) -> dict:
    """Run UX/Vision agent to analyze screenshots for UX issues."""
    from app.agents.ux_vision import run_ux_vision

    _notify(state, "ux_vision", "running", 35)

    try:
        result = _run_with_timeout(run_ux_vision, args=(state,))
    except (_AgentTimeoutError, Exception) as exc:
        logger.error("UX vision agent failed: %s", exc)
        result = {"ux_issues": [], "ux_score": 50, "mobile_score": 50, "accessibility_score": 50}

    _persist_agent_output(state, "ux_vision", result)
    _notify(state, "ux_vision", "complete", 50)

    return {
        "ux_issues": result.get("ux_issues", []),
        "ux_score": result.get("ux_score", 50),
        "mobile_score": result.get("mobile_score", 50),
        "accessibility_score": result.get("accessibility_score", 50),
    }


def copy_content_node(state: AuditState) -> dict:
    """Run Copy/Content agent to analyze page copy."""
    from app.agents.copy_content import run_copy_content

    _notify(state, "copy_content", "running", 35)

    try:
        result = _run_with_timeout(run_copy_content, args=(state,))
    except (_AgentTimeoutError, Exception) as exc:
        logger.error("Copy content agent failed: %s", exc)
        result = {"copy_issues": [], "persuasion_score": 50, "readability_score": 50, "emotional_trigger_map": {}}

    _persist_agent_output(state, "copy_content", result)
    _notify(state, "copy_content", "complete", 60)

    return {
        "copy_issues": result.get("copy_issues", []),
        "persuasion_score": result.get("persuasion_score", 50),
        "readability_score": result.get("readability_score", 50),
        "emotional_trigger_map": result.get("emotional_trigger_map", {}),
    }


def data_performance_node(state: AuditState) -> dict:
    """Run Data/Performance agent for SEO and revenue analysis."""
    from app.agents.data_performance import run_data_performance

    _notify(state, "data_performance", "running", 35)

    try:
        result = _run_with_timeout(run_data_performance, args=(state,))
    except (_AgentTimeoutError, Exception) as exc:
        logger.error("Data performance agent failed: %s", exc)
        result = {"performance_data": {}, "seo_issues": [], "revenue_leak_monthly": 0, "revenue_leak_confidence": "Estimated", "revenue_leak_assumptions": {}}

    _persist_agent_output(state, "data_performance", result)
    _notify(state, "data_performance", "complete", 70)

    return {
        "performance_data": result.get("performance_data", {}),
        "seo_issues": result.get("seo_issues", []),
        "revenue_leak_monthly": result.get("revenue_leak_monthly", 0),
        "revenue_leak_confidence": result.get("revenue_leak_confidence", "Estimated"),
        "revenue_leak_assumptions": result.get("revenue_leak_assumptions", {}),
    }


def orchestrator_synthesis(state: AuditState) -> dict:
    """Synthesize all agent outputs into final CRO score and issue list.

    CRO Score calculation (from spec):
    - UX & Friction: 25%
    - Copy & Persuasion: 20%
    - Performance & CWV: 20%
    - SEO: 15%
    - Conversion Psychology: 10%
    - Accessibility: 10%
    """
    _notify(state, "synthesis", "running", 80)

    # Collect component scores (default to 50 if missing)
    ux_score = state.get("ux_score", 50)
    persuasion_score = state.get("persuasion_score", 50)
    perf_data = state.get("performance_data", {})
    performance_score = perf_data.get("performance_score", 50)
    seo_score = perf_data.get("seo_score", 50)
    accessibility_score = state.get("accessibility_score", 50)

    # Conversion psychology is average of UX and copy persuasion
    conversion_psychology = (ux_score + persuasion_score) // 2

    # Weighted CRO score
    cro_score = int(
        ux_score * CRO_WEIGHTS["ux_friction"]
        + persuasion_score * CRO_WEIGHTS["copy_persuasion"]
        + performance_score * CRO_WEIGHTS["performance_cwv"]
        + seo_score * CRO_WEIGHTS["seo"]
        + conversion_psychology * CRO_WEIGHTS["conversion_psychology"]
        + accessibility_score * CRO_WEIGHTS["accessibility"]
    )

    # Clamp to 0-100
    cro_score = max(0, min(100, cro_score))

    # Merge all issues from all agents
    all_issues: list[dict] = []
    all_issues.extend(state.get("ux_issues", []))
    all_issues.extend(state.get("copy_issues", []))
    all_issues.extend(state.get("seo_issues", []))

    # Calculate ICE score for each issue and sort by it
    for issue in all_issues:
        impact = issue.get("impact_score", 5)
        confidence = issue.get("confidence_score", 5)
        effort = issue.get("effort_score", 5)
        # ICE = (Impact * Confidence) / Effort — higher is better priority
        issue["ice_score"] = round((impact * confidence) / max(effort, 1), 2)

    # Sort by ICE score descending (highest priority first)
    all_issues.sort(key=lambda x: x.get("ice_score", 0), reverse=True)

    # Build final agent_outputs summary
    agent_outputs = {
        "site_intelligence": state.get("site_intelligence_output", {}),
        "ux_vision": {
            "ux_score": ux_score,
            "mobile_score": state.get("mobile_score", 50),
            "accessibility_score": accessibility_score,
            "issues_count": len(state.get("ux_issues", [])),
        },
        "copy_content": {
            "persuasion_score": persuasion_score,
            "readability_score": state.get("readability_score", 50),
            "emotional_trigger_map": state.get("emotional_trigger_map", {}),
            "issues_count": len(state.get("copy_issues", [])),
        },
        "data_performance": {
            "seo_score": seo_score,
            "performance_score": performance_score,
            "seo_checklist": perf_data.get("seo_checklist", {}),
            "issues_count": len(state.get("seo_issues", [])),
        },
        "score_breakdown": {
            "ux_friction": ux_score,
            "copy_persuasion": persuasion_score,
            "performance_cwv": performance_score,
            "seo": seo_score,
            "conversion_psychology": conversion_psychology,
            "accessibility": accessibility_score,
        },
        "issues": all_issues,
        "revenue_leak": {
            "monthly": state.get("revenue_leak_monthly", 0),
            "confidence": state.get("revenue_leak_confidence", "Estimated"),
            "assumptions": state.get("revenue_leak_assumptions", {}),
        },
    }

    _notify(state, "synthesis", "complete", 95)

    logger.info(
        "Synthesis complete: cro_score=%d issues=%d revenue_leak=$%s",
        cro_score, len(all_issues), state.get("revenue_leak_monthly", 0),
    )

    return {
        "cro_score": cro_score,
        "issues": all_issues,
        "agent_outputs": agent_outputs,
    }


# ═══════════════════════════════════════
# LangGraph StateGraph builder
# ═══════════════════════════════════════

def _build_graph() -> StateGraph:
    """Build the LangGraph StateGraph for the audit pipeline."""
    graph = StateGraph(AuditState)

    # Add nodes
    graph.add_node("orchestrator_init", orchestrator_init)
    graph.add_node("site_intelligence", site_intelligence_node)
    graph.add_node("ux_vision", ux_vision_node)
    graph.add_node("copy_content", copy_content_node)
    graph.add_node("data_performance", data_performance_node)
    graph.add_node("orchestrator_synthesis", orchestrator_synthesis)

    # Define edges — pipeline order
    graph.set_entry_point("orchestrator_init")
    graph.add_edge("orchestrator_init", "site_intelligence")

    # After site intelligence, run UX/Copy/Data in parallel
    # LangGraph handles fan-out when multiple edges leave a node
    graph.add_edge("site_intelligence", "ux_vision")
    graph.add_edge("site_intelligence", "copy_content")
    graph.add_edge("site_intelligence", "data_performance")

    # All three converge into synthesis
    graph.add_edge("ux_vision", "orchestrator_synthesis")
    graph.add_edge("copy_content", "orchestrator_synthesis")
    graph.add_edge("data_performance", "orchestrator_synthesis")

    # Synthesis -> END
    graph.add_edge("orchestrator_synthesis", END)

    return graph


def run_audit_pipeline(
    audit_id: str,
    org_id: str,
    url: str,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    """Run the full LangGraph agent pipeline for an audit.

    Args:
        audit_id: The audit record ID.
        org_id: The organization ID (for data isolation).
        url: The target URL to audit.
        progress_callback: Optional callback(audit_id, agent, status, progress)
            used by the Celery task to publish real-time progress.

    Returns:
        Final state dict with cro_score, issues, agent_outputs, etc.
    """
    logger.info("Starting audit pipeline: audit_id=%s url=%s", audit_id, url)
    start = time.time()

    # Build and compile the graph
    graph = _build_graph()
    app = graph.compile()

    # Initialize state
    initial_state: AuditState = {
        "audit_id": audit_id,
        "org_id": org_id,
        "url": url,
        "pages": [],
        "ga4_connected": False,
        "gsc_connected": False,
        "github_connected": False,
        "progress_callback": progress_callback,
    }

    # Run the graph
    final_state = app.invoke(initial_state)

    elapsed = round(time.time() - start, 1)
    logger.info(
        "Audit pipeline complete: audit_id=%s cro_score=%s issues=%d elapsed=%ss",
        audit_id,
        final_state.get("cro_score"),
        len(final_state.get("issues", [])),
        elapsed,
    )

    # Persist issues to Supabase
    _persist_issues(final_state)

    return final_state


def _persist_issues(state: AuditState) -> None:
    """Write all detected issues to the Supabase issues table."""
    try:
        from app.db.supabase import get_supabase_client

        supabase = get_supabase_client()
        audit_id = state["audit_id"]
        org_id = state["org_id"]
        issues = state.get("issues", [])

        if not issues:
            return

        rows = []
        for issue in issues:
            rows.append({
                "audit_id": audit_id,
                "org_id": org_id,
                "agent": issue.get("agent"),
                "severity": issue.get("severity"),
                "category": issue.get("category"),
                "title": issue.get("title", "Untitled issue"),
                "description": issue.get("description"),
                "recommendation": issue.get("recommendation"),
                "affected_element": issue.get("affected_element"),
                "ice_score": issue.get("ice_score"),
                "impact_score": issue.get("impact_score"),
                "confidence_score": issue.get("confidence_score"),
                "effort_score": issue.get("effort_score"),
                "ab_variants": issue.get("ab_variants", []),
                "status": "open",
            })

        supabase.table("issues").insert(rows).execute()
        logger.info("Persisted %d issues for audit %s", len(rows), audit_id)

    except Exception as exc:
        logger.error("Failed to persist issues: %s", exc, exc_info=True)
