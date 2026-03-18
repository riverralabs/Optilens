"""Data/Performance agent — Core Web Vitals, SEO analysis, revenue benchmarks.

Phase 1 simplified version: analyzes DOM for basic SEO signals and uses
industry benchmarks for revenue leak estimation (labeled as Estimated).
Full Lighthouse/PageSpeed integration in Phase 2.
"""

from __future__ import annotations

import json
import logging

import anthropic

from app.agents.orchestrator import AuditState

logger = logging.getLogger("optilens.agents.data_performance")

# Industry benchmarks for revenue leak estimation (Phase 1)
BENCHMARKS: dict[str, dict] = {
    "ecommerce": {
        "avg_cart_abandonment": 0.70,
        "avg_order_value": 85.0,
        "avg_conversion_rate": 0.025,
        "monthly_sessions_estimate": 10000,
    },
    "saas": {
        "avg_trial_to_paid": 0.04,
        "avg_mrr_per_customer": 120.0,
        "avg_conversion_rate": 0.03,
        "monthly_sessions_estimate": 5000,
    },
    "landing_page": {
        "avg_conversion_rate": 0.025,
        "avg_lead_value": 50.0,
        "monthly_sessions_estimate": 8000,
    },
    "corporate": {
        "avg_lead_rate": 0.018,
        "avg_lead_value": 200.0,
        "monthly_sessions_estimate": 3000,
    },
    "webapp": {
        "avg_conversion_rate": 0.05,
        "avg_revenue_per_user": 30.0,
        "monthly_sessions_estimate": 15000,
    },
}

SYSTEM_PROMPT = """You are a Data/Performance analyst for Optilens, an AI-powered CRO audit platform.

You analyze website HTML for SEO issues, performance signals, and technical problems.
You MUST respond with a valid JSON object (no markdown, no explanation outside the JSON).

Evaluate:
- Title tag: present, correct length (50-60 chars), keyword-optimized
- Meta description: present, correct length (150-160 chars), compelling
- H1 tags: exactly one per page, keyword-relevant
- Schema markup: is structured data present (JSON-LD)?
- Image optimization: alt tags, lazy loading, size indicators
- Internal linking: navigation structure, orphaned pages
- Mobile meta: viewport tag present and correct
- Open Graph / Twitter cards: social sharing metadata
- Canonical URLs: present and correct
- Core Web Vitals indicators from DOM (loading patterns, render-blocking resources)

For each issue, provide severity and specific fix.

Respond with EXACTLY this JSON format:
{
  "issues": [
    {
      "title": "Short issue title",
      "description": "Why this is a problem",
      "severity": "critical|high|medium|low",
      "category": "seo_title|seo_meta|seo_headings|seo_schema|seo_images|seo_links|seo_mobile|performance|cwv",
      "recommendation": "Specific fix",
      "affected_element": "Element or tag affected",
      "impact_score": 7,
      "confidence_score": 9,
      "effort_score": 2
    }
  ],
  "seo_score": 60,
  "performance_score": 55,
  "seo_checklist": {
    "title_tag": true,
    "meta_description": true,
    "h1_present": true,
    "h1_single": false,
    "schema_markup": false,
    "viewport_meta": true,
    "canonical_url": false,
    "og_tags": false,
    "image_alt_tags": false,
    "robots_meta": true
  },
  "summary": "Brief performance/SEO assessment"
}

Impact/confidence/effort scores are 1-10."""


def run_data_performance(state: AuditState) -> dict:
    """Analyze DOM for SEO/performance issues and estimate revenue leak.

    Phase 1: DOM-based SEO analysis + industry benchmark revenue estimation.
    Phase 2 will add Lighthouse CI, PageSpeed API, and real GA4 data.

    Returns dict with performance issues, scores, and revenue estimates.
    """
    url = state["url"]
    dom_content = state.get("dom_content", {})
    site_type = state.get("site_type", "landing_page")
    framework = state.get("framework", [])

    # Run Claude-based SEO analysis
    seo_result = _analyze_seo(url, dom_content, site_type, framework)

    # Calculate benchmark revenue leak (Phase 1 — always labeled as Estimated)
    revenue_data = _estimate_revenue_leak(site_type, seo_result.get("seo_score", 50))

    # Merge SEO issues with performance agent tag
    issues = seo_result.get("issues", [])
    for issue in issues:
        if issue.get("category", "").startswith("seo_"):
            issue["agent"] = "seo"
        else:
            issue["agent"] = "performance"

    logger.info(
        "Data/Performance analysis complete: %d issues, seo=%s, revenue_leak=$%s url=%s",
        len(issues), seo_result.get("seo_score"), revenue_data.get("monthly_leak"), url,
    )

    return {
        "performance_data": {
            "seo_score": seo_result.get("seo_score", 50),
            "performance_score": seo_result.get("performance_score", 50),
            "seo_checklist": seo_result.get("seo_checklist", {}),
            "summary": seo_result.get("summary", ""),
        },
        "seo_issues": issues,
        "revenue_leak_monthly": revenue_data["monthly_leak"],
        "revenue_leak_confidence": "Estimated",
        "revenue_leak_assumptions": revenue_data["assumptions"],
    }


def _analyze_seo(url: str, dom_content: dict, site_type: str, framework: list) -> dict:
    """Run Claude-based SEO/performance analysis on DOM content."""
    if not dom_content:
        logger.warning("No DOM content for SEO analysis: %s", url)
        return {
            "issues": [],
            "seo_score": 50,
            "performance_score": 50,
            "seo_checklist": {},
            "summary": "No content available for analysis",
        }

    # Build analysis text
    analysis_text = ""
    for page_url, html in dom_content.items():
        truncated = html[:12000] if len(html) > 12000 else html
        analysis_text += f"--- Page: {page_url} ---\n{truncated}\n\n"

    client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Analyze this website for SEO and performance issues.\n"
                        f"URL: {url}\n"
                        f"Site type: {site_type}\n"
                        f"CRO framework: {', '.join(framework)}\n\n"
                        f"HTML content:\n{analysis_text}"
                    ),
                }
            ],
        )

        result_text = response.content[0].text.strip()

        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        return json.loads(result_text)

    except Exception as exc:
        logger.error("SEO analysis failed: %s", exc, exc_info=True)
        return {
            "issues": [],
            "seo_score": 50,
            "performance_score": 50,
            "seo_checklist": {},
            "summary": f"SEO analysis failed: {exc}",
        }


def _estimate_revenue_leak(site_type: str, seo_score: int) -> dict:
    """Estimate monthly revenue leak using industry benchmarks.

    Phase 1 only — always labeled as 'Estimated'.
    Phase 2 will use real GA4 data when available.

    Every figure MUST have calculation_basis and confidence labels.
    """
    benchmarks = BENCHMARKS.get(site_type, BENCHMARKS["landing_page"])

    # The revenue leak is proportional to how far below optimal the site scores
    # A site scoring 50/100 has ~50% improvement potential on its conversion funnel
    improvement_potential = max(0, (100 - seo_score)) / 100

    if site_type == "ecommerce":
        sessions = benchmarks["monthly_sessions_estimate"]
        aov = benchmarks["avg_order_value"]
        abandonment = benchmarks["avg_cart_abandonment"]
        # Revenue leaked = sessions * abandonment_rate * AOV * improvement_potential * 0.15
        monthly_leak = round(sessions * abandonment * aov * improvement_potential * 0.15, 2)
        assumptions = {
            "monthly_sessions": sessions,
            "avg_order_value": aov,
            "cart_abandonment_rate": abandonment,
            "improvement_potential": round(improvement_potential, 2),
        }

    elif site_type == "saas":
        sessions = benchmarks["monthly_sessions_estimate"]
        mrr = benchmarks["avg_mrr_per_customer"]
        trial_rate = benchmarks["avg_trial_to_paid"]
        monthly_leak = round(sessions * (1 - trial_rate) * mrr * improvement_potential * 0.15, 2)
        assumptions = {
            "monthly_sessions": sessions,
            "avg_mrr_per_customer": mrr,
            "trial_to_paid_rate": trial_rate,
            "improvement_potential": round(improvement_potential, 2),
        }

    else:
        sessions = benchmarks["monthly_sessions_estimate"]
        conversion = benchmarks.get("avg_conversion_rate", 0.025)
        value = benchmarks.get("avg_lead_value", benchmarks.get("avg_revenue_per_user", 50))
        monthly_leak = round(sessions * (1 - conversion) * value * improvement_potential * 0.15, 2)
        assumptions = {
            "monthly_sessions": sessions,
            "avg_conversion_rate": conversion,
            "avg_value_per_conversion": value,
            "improvement_potential": round(improvement_potential, 2),
        }

    # Cap at reasonable maximum to avoid unrealistic estimates
    monthly_leak = min(monthly_leak, 500000)

    assumptions["calculation_basis"] = "benchmark_estimate"
    assumptions["confidence"] = "Estimated"
    assumptions["label"] = "Benchmark estimate — connect GA4 for real figures"

    return {
        "monthly_leak": monthly_leak,
        "assumptions": assumptions,
    }
