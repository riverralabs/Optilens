"""UX/Vision agent — screenshot analysis, WCAG violations, friction detection.

Uses Claude vision to analyze desktop and mobile screenshots for UX issues.
Checks visual hierarchy, CTA placement, form friction, and mobile responsiveness.
"""

from __future__ import annotations

import json
import logging

import anthropic

from app.agents.orchestrator import AuditState

logger = logging.getLogger("optilens.agents.ux_vision")

SYSTEM_PROMPT = """You are a UX/Vision analyst for Optilens, an AI-powered CRO audit platform.

You analyze website screenshots to identify UX issues that hurt conversions.
You MUST respond with a valid JSON object (no markdown, no explanation outside the JSON).

For each issue found, assess:
- Visual hierarchy: Is the most important content prominent?
- CTA placement: Are CTAs visible, clear, and well-positioned?
- Form friction: Are forms simple, with clear labels and minimal fields?
- Mobile responsiveness: Does the layout work on mobile?
- Accessibility (WCAG 2.2): Color contrast, text size, touch targets
- Cognitive load: Is the page overwhelming or cluttered?
- Trust signals: Are there reviews, badges, guarantees visible?

Severity levels:
- critical: Blocks conversions entirely (broken CTA, invisible form)
- high: Significantly reduces conversions (poor CTA visibility, confusing layout)
- medium: Impacts some users (minor readability issues, suboptimal spacing)
- low: Nice to have (minor alignment, small visual improvements)

Respond with EXACTLY this JSON format:
{
  "issues": [
    {
      "title": "Short issue title",
      "description": "Detailed description of the problem",
      "severity": "critical|high|medium|low",
      "category": "visual_hierarchy|cta_placement|form_friction|mobile|accessibility|cognitive_load|trust_signals",
      "recommendation": "Specific actionable fix",
      "affected_element": "CSS selector or description of the element",
      "coordinates": {"x": 0, "y": 0, "width": 100, "height": 50},
      "impact_score": 8,
      "confidence_score": 7,
      "effort_score": 3
    }
  ],
  "ux_score": 65,
  "mobile_score": 70,
  "accessibility_score": 55,
  "summary": "Brief overall UX assessment"
}

Impact/confidence/effort scores are 1-10 (10 = highest). Be specific and actionable."""


def run_ux_vision(state: AuditState) -> dict:
    """Analyze screenshots with Claude vision for UX issues.

    Args:
        state: AuditState with screenshots dict (url -> base64 PNG).

    Returns dict with issues list, scores, and summary.
    """
    url = state["url"]
    screenshots = state.get("screenshots", {})
    site_type = state.get("site_type", "landing_page")
    framework = state.get("framework", [])

    if not screenshots:
        logger.warning("No screenshots available for UX analysis: %s", url)
        return {
            "ux_issues": [],
            "ux_score": 50,
            "mobile_score": 50,
            "accessibility_score": 50,
            "summary": "No screenshots available for analysis",
        }

    client = anthropic.Anthropic()

    # Build message content with screenshots
    content: list[dict] = [
        {
            "type": "text",
            "text": (
                f"Analyze this website for UX/conversion issues.\n"
                f"URL: {url}\n"
                f"Site type: {site_type}\n"
                f"CRO framework: {', '.join(framework)}\n\n"
                f"Look for issues in: visual hierarchy, CTA placement, form friction, "
                f"mobile responsiveness, accessibility (WCAG 2.2), cognitive load, "
                f"and trust signals."
            ),
        }
    ]

    # Add up to 4 screenshots (to stay within token limits)
    screenshot_count = 0
    for page_url, b64_image in screenshots.items():
        if screenshot_count >= 4:
            break
        content.append({"type": "text", "text": f"\nScreenshot of {page_url}:"})
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": b64_image,
            },
        })
        screenshot_count += 1

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
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
            issue["agent"] = "ux"

        logger.info(
            "UX analysis complete: %d issues found, ux_score=%s url=%s",
            len(issues), result.get("ux_score"), url,
        )

        return {
            "ux_issues": issues,
            "ux_score": result.get("ux_score", 50),
            "mobile_score": result.get("mobile_score", 50),
            "accessibility_score": result.get("accessibility_score", 50),
            "summary": result.get("summary", ""),
        }

    except Exception as exc:
        logger.error("UX Vision agent failed: %s", exc, exc_info=True)
        return {
            "ux_issues": [],
            "ux_score": 50,
            "mobile_score": 50,
            "accessibility_score": 50,
            "summary": f"UX analysis failed: {exc}",
        }
