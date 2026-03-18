"""Copy/Content agent — persuasion scoring, rewrites, A/B variants.

Analyzes page copy, headlines, CTAs. Scores persuasion using the detected
CRO framework. Generates A/B variants for critical CTAs and rewrite
suggestions for weak copy.
"""

from __future__ import annotations

import json
import logging

import anthropic

from app.agents.orchestrator import AuditState

logger = logging.getLogger("optilens.agents.copy_content")

SYSTEM_PROMPT = """You are a Copy/Content analyst for Optilens, an AI-powered CRO audit platform.

You analyze website copy to identify conversion-killing text and generate improvements.
You MUST respond with a valid JSON object (no markdown, no explanation outside the JSON).

Evaluate:
- Headlines: Are they benefit-driven, clear, and compelling?
- CTAs: Are they action-oriented, specific, and urgency-creating?
- Body copy: Is it scannable, persuasion-focused, and concise?
- Social proof: Are testimonials, reviews, case studies present and effective?
- Objection handling: Does the copy address common buyer hesitations?
- Readability: Flesch-Kincaid score, sentence length, jargon level
- Emotional triggers: Fear of missing out, social proof, authority, scarcity

For each critical/high CTA issue, generate exactly 2 A/B variant rewrites.

Respond with EXACTLY this JSON format:
{
  "issues": [
    {
      "title": "Short issue title",
      "description": "Why this copy hurts conversions",
      "severity": "critical|high|medium|low",
      "category": "headline|cta|body_copy|social_proof|objection_handling|readability|meta",
      "recommendation": "Specific rewrite suggestion",
      "affected_element": "The original text or CSS selector",
      "ab_variants": [
        {"variant": "A", "text": "Rewritten version A"},
        {"variant": "B", "text": "Rewritten version B"}
      ],
      "impact_score": 8,
      "confidence_score": 7,
      "effort_score": 2
    }
  ],
  "persuasion_score": 55,
  "readability_score": 65,
  "emotional_trigger_map": {
    "urgency": 3,
    "social_proof": 5,
    "authority": 4,
    "scarcity": 2,
    "reciprocity": 3
  },
  "summary": "Brief overall copy assessment"
}

Impact/confidence/effort scores are 1-10. Only include ab_variants for critical/high issues.
Emotional trigger map values are 1-10 (10 = strong presence)."""


def run_copy_content(state: AuditState) -> dict:
    """Analyze page copy for persuasion effectiveness and generate improvements.

    Args:
        state: AuditState with dom_content dict (url -> HTML string).

    Returns dict with copy issues, scores, A/B variants, and emotional trigger map.
    """
    url = state["url"]
    dom_content = state.get("dom_content", {})
    site_type = state.get("site_type", "landing_page")
    framework = state.get("framework", [])

    if not dom_content:
        logger.warning("No DOM content available for copy analysis: %s", url)
        return {
            "copy_issues": [],
            "persuasion_score": 50,
            "readability_score": 50,
            "emotional_trigger_map": {},
            "summary": "No content available for analysis",
        }

    # Extract text content from DOM (truncate to fit token budget)
    analysis_text = ""
    for page_url, html in dom_content.items():
        truncated = html[:10000] if len(html) > 10000 else html
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
                        f"Analyze the copy/content on this website for conversion effectiveness.\n"
                        f"URL: {url}\n"
                        f"Site type: {site_type}\n"
                        f"CRO framework: {', '.join(framework)}\n\n"
                        f"Page content:\n{analysis_text}"
                    ),
                }
            ],
        )

        result_text = response.content[0].text.strip()

        # Parse JSON — handle markdown wrapping
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result = json.loads(result_text)

        issues = result.get("issues", [])

        # Tag each issue with the agent name
        for issue in issues:
            issue["agent"] = "copy"

        logger.info(
            "Copy analysis complete: %d issues found, persuasion=%s url=%s",
            len(issues), result.get("persuasion_score"), url,
        )

        return {
            "copy_issues": issues,
            "persuasion_score": result.get("persuasion_score", 50),
            "readability_score": result.get("readability_score", 50),
            "emotional_trigger_map": result.get("emotional_trigger_map", {}),
            "summary": result.get("summary", ""),
        }

    except Exception as exc:
        logger.error("Copy/Content agent failed: %s", exc, exc_info=True)
        return {
            "copy_issues": [],
            "persuasion_score": 50,
            "readability_score": 50,
            "emotional_trigger_map": {},
            "summary": f"Copy analysis failed: {exc}",
        }
