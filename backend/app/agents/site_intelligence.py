"""Site Intelligence agent — detects site type and selects CRO framework.

Analyzes DOM content, URL structure, and page copy to classify the site type.
Maps the detected type to the appropriate CRO framework(s). All other agents
wait for this agent's output before running.
"""

from __future__ import annotations

import json
import logging

import anthropic

from app.agents.orchestrator import AuditState

logger = logging.getLogger("optilens.agents.site_intelligence")

# Framework mapping by site type
FRAMEWORK_MAP: dict[str, list[str]] = {
    "ecommerce": ["Baymard", "PIE"],
    "saas": ["JTBD", "LIFT"],
    "landing_page": ["AIDA", "PAS"],
    "corporate": ["ResearchXL", "Trust Signals"],
    "webapp": ["Cognitive Load", "WCAG 2.2"],
}

VALID_SITE_TYPES = set(FRAMEWORK_MAP.keys())

# Primary KPI mapping
KPI_MAP: dict[str, str] = {
    "ecommerce": "revenue_per_session",
    "saas": "trial_to_paid_conversion",
    "landing_page": "cta_conversion_rate",
    "corporate": "lead_generation_rate",
    "webapp": "task_completion_rate",
}

SYSTEM_PROMPT = """You are a Site Intelligence analyst for Optilens, a CRO audit platform.

Your task is to analyze website content and classify the site type. You MUST respond
with a valid JSON object (no markdown, no explanation outside the JSON).

Site types: ecommerce, saas, landing_page, corporate, webapp

Analyze these signals:
- URL structure (e.g. /products, /pricing, /blog)
- Page content and copy tone
- Navigation patterns
- CTAs and conversion elements
- E-commerce indicators (cart, checkout, product pages)
- SaaS indicators (pricing tiers, free trial, sign up)

Respond with EXACTLY this JSON format:
{
  "site_type": "one of: ecommerce|saas|landing_page|corporate|webapp",
  "confidence": 85,
  "reasoning": "Brief explanation of classification signals",
  "primary_kpi": "The main KPI this site should optimize for",
  "key_signals": ["signal1", "signal2", "signal3"]
}

The confidence score should be 0-100. Be honest about uncertainty."""


def run_site_intelligence(state: AuditState) -> dict:
    """Detect site type from DOM + copy + URL structure, select CRO framework.

    Returns a dict with site_type, framework, confidence, and primary_kpi.
    If confidence < 70%, adds a flag for the report.
    """
    url = state["url"]
    dom_content = state.get("dom_content", {})
    page_metadata = state.get("screenshots", {})  # metadata passed via state

    # Build analysis content from available DOM
    analysis_text = f"URL: {url}\n\n"
    for page_url, html in dom_content.items():
        # Send a truncated version to avoid token limits
        truncated = html[:8000] if len(html) > 8000 else html
        analysis_text += f"--- Page: {page_url} ---\n{truncated}\n\n"

    if not analysis_text.strip() or len(dom_content) == 0:
        analysis_text += "No DOM content available. Classify based on URL structure only."

    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this website and classify its type:\n\n{analysis_text}",
                }
            ],
        )

        result_text = response.content[0].text.strip()

        # Parse JSON response — handle potential markdown wrapping
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result = json.loads(result_text)

        site_type = result.get("site_type", "landing_page")
        confidence = result.get("confidence", 50)

        # Validate site type
        if site_type not in VALID_SITE_TYPES:
            logger.warning("Invalid site_type '%s', defaulting to landing_page", site_type)
            site_type = "landing_page"
            confidence = min(confidence, 40)

        framework = FRAMEWORK_MAP[site_type]
        primary_kpi = KPI_MAP.get(site_type, "conversion_rate")

        # Flag low confidence
        low_confidence_flag = None
        if confidence < 70:
            low_confidence_flag = "Site type estimated — review recommended"
            logger.warning(
                "Low confidence site classification: type=%s confidence=%d url=%s",
                site_type, confidence, url,
            )

        logger.info(
            "Site classified: type=%s confidence=%d framework=%s url=%s",
            site_type, confidence, framework, url,
        )

        return {
            "site_type": site_type,
            "framework": framework,
            "primary_kpi": primary_kpi,
            "confidence": confidence,
            "reasoning": result.get("reasoning", ""),
            "key_signals": result.get("key_signals", []),
            "low_confidence_flag": low_confidence_flag,
        }

    except Exception as exc:
        logger.error("Site Intelligence failed: %s", exc, exc_info=True)
        # Fallback — default to landing_page with low confidence
        return {
            "site_type": "landing_page",
            "framework": FRAMEWORK_MAP["landing_page"],
            "primary_kpi": KPI_MAP["landing_page"],
            "confidence": 30,
            "reasoning": f"Classification failed ({exc}), using default",
            "key_signals": [],
            "low_confidence_flag": "Site type estimated — classification failed, review recommended",
        }
