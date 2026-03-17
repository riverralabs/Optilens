"""Site Intelligence agent — detects site type and selects CRO framework.

Full implementation in Step 1.6.
"""

from __future__ import annotations

import logging

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
