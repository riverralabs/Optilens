"""Playwright crawler service — screenshots and DOM extraction.

Full implementation in Step 1.5.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("optilens.services.crawler")

# Desktop viewport: 1440x900
DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
# Mobile viewport: 375x812
MOBILE_VIEWPORT = {"width": 375, "height": 812}
# Max DOM nodes to extract
MAX_DOM_NODES = 5000
# Timeout per page
PAGE_TIMEOUT_MS = 30_000
# Max redirects to follow
MAX_REDIRECTS = 3
# User agent
USER_AGENT = "Optilensbot/1.0 (+https://optilens.ai/bot)"
