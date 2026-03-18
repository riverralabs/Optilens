"""Playwright crawler service — screenshots and DOM extraction.

Crawls target URLs using headless Chromium, captures full-page screenshots,
extracts DOM content and page metadata. Handles errors gracefully so a
single failing page never crashes the entire audit.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeout,
    sync_playwright,
)

logger = logging.getLogger("optilens.services.crawler")

# Desktop viewport: 1440x900
DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
# Mobile viewport: 375x812
MOBILE_VIEWPORT = {"width": 375, "height": 812}
# Max DOM nodes to extract — cap to keep payloads manageable
MAX_DOM_NODES = 5000
# Timeout per page in milliseconds
PAGE_TIMEOUT_MS = 30_000
# Max redirects to follow
MAX_REDIRECTS = 3
# User agent string
USER_AGENT = "Mozilla/5.0 (compatible; Optilensbot/1.0; +https://optilens.ai/bot)"


@dataclass
class PageMetadata:
    """Metadata extracted from a single crawled page."""

    title: str = ""
    meta_description: str = ""
    h1s: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    status_code: int = 0
    is_partial: bool = False
    error: str | None = None


@dataclass
class CrawlResult:
    """Complete crawl output for all pages."""

    screenshots: dict[str, str] = field(default_factory=dict)        # url -> base64 PNG
    mobile_screenshots: dict[str, str] = field(default_factory=dict)  # url -> base64 PNG
    dom_content: dict[str, str] = field(default_factory=dict)         # url -> HTML string
    page_metadata: dict[str, dict] = field(default_factory=dict)      # url -> metadata dict
    errors: dict[str, str] = field(default_factory=dict)              # url -> error message


def crawl_pages(url: str, pages_to_crawl: list[str] | None = None) -> CrawlResult:
    """Crawl one or more pages and return screenshots, DOM content, and metadata.

    Args:
        url: The primary URL to crawl.
        pages_to_crawl: Optional list of additional page URLs. If None,
            only the primary URL is crawled.

    Returns:
        CrawlResult with screenshots, DOM content, and metadata for each page.
    """
    # Build the full page list — primary URL always included
    all_pages = [url]
    if pages_to_crawl:
        for page_url in pages_to_crawl:
            # Resolve relative URLs against the primary URL
            resolved = urljoin(url, page_url) if not page_url.startswith("http") else page_url
            if resolved not in all_pages:
                all_pages.append(resolved)

    result = CrawlResult()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        try:
            for page_url in all_pages:
                _crawl_single_page(browser, page_url, result)
        finally:
            browser.close()

    logger.info(
        "Crawl complete: %d pages, %d screenshots, %d errors",
        len(all_pages), len(result.screenshots), len(result.errors),
    )
    return result


def _crawl_single_page(browser: Browser, url: str, result: CrawlResult) -> None:
    """Crawl a single page, capturing desktop + mobile screenshots and DOM."""
    logger.info("Crawling: %s", url)

    # -- Desktop pass --
    context = browser.new_context(
        viewport=DESKTOP_VIEWPORT,
        user_agent=USER_AGENT,
    )
    page = context.new_page()

    try:
        response = page.goto(
            url,
            wait_until="networkidle",
            timeout=PAGE_TIMEOUT_MS,
        )

        status_code = response.status if response else 0

        # Handle HTTP errors gracefully
        if status_code >= 400:
            logger.warning("HTTP %d for %s", status_code, url)
            result.errors[url] = f"HTTP {status_code}"
            meta = PageMetadata(status_code=status_code, error=f"HTTP {status_code}")
            result.page_metadata[url] = _metadata_to_dict(meta)
            return

        # Check for auth walls (login forms, access denied patterns)
        if _is_behind_auth(page):
            logger.warning("Page appears to be behind auth: %s", url)
            meta = PageMetadata(
                status_code=status_code,
                is_partial=True,
                error="Page appears to require authentication — auditing public content only",
            )
            result.page_metadata[url] = _metadata_to_dict(meta)

        # Extract metadata
        metadata = _extract_metadata(page, status_code)
        result.page_metadata[url] = _metadata_to_dict(metadata)

        # Extract DOM content (capped at MAX_DOM_NODES)
        dom_html = _extract_dom(page)
        result.dom_content[url] = dom_html

        # Desktop screenshot
        try:
            screenshot_bytes = page.screenshot(full_page=True, type="png")
            result.screenshots[url] = base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as exc:
            logger.warning("Desktop screenshot failed for %s: %s", url, exc)
            metadata.is_partial = True
            result.page_metadata[url] = _metadata_to_dict(metadata)

    except PlaywrightTimeout:
        logger.warning("Timeout crawling %s (>%dms)", url, PAGE_TIMEOUT_MS)
        result.errors[url] = f"Timeout after {PAGE_TIMEOUT_MS}ms"
        meta = PageMetadata(error=f"Timeout after {PAGE_TIMEOUT_MS}ms", is_partial=True)
        result.page_metadata[url] = _metadata_to_dict(meta)

    except Exception as exc:
        logger.error("Failed to crawl %s: %s", url, exc)
        result.errors[url] = str(exc)
        meta = PageMetadata(error=str(exc))
        result.page_metadata[url] = _metadata_to_dict(meta)

    finally:
        context.close()

    # -- Mobile pass --
    mobile_context = browser.new_context(
        viewport=MOBILE_VIEWPORT,
        user_agent=USER_AGENT,
        is_mobile=True,
    )
    mobile_page = mobile_context.new_page()

    try:
        mobile_page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)
        screenshot_bytes = mobile_page.screenshot(full_page=True, type="png")
        result.mobile_screenshots[url] = base64.b64encode(screenshot_bytes).decode("utf-8")
    except Exception as exc:
        logger.warning("Mobile screenshot failed for %s: %s", url, exc)
    finally:
        mobile_context.close()


def _extract_metadata(page: Page, status_code: int) -> PageMetadata:
    """Extract title, meta description, H1s, and internal links from a page."""
    try:
        title = page.title() or ""

        meta_desc = page.evaluate("""
            () => {
                const el = document.querySelector('meta[name="description"]');
                return el ? el.getAttribute('content') || '' : '';
            }
        """)

        h1s = page.evaluate("""
            () => Array.from(document.querySelectorAll('h1')).map(el => el.innerText.trim()).filter(Boolean)
        """)

        links = page.evaluate("""
            () => {
                const anchors = document.querySelectorAll('a[href]');
                const hrefs = new Set();
                anchors.forEach(a => {
                    const href = a.href;
                    if (href && href.startsWith('http')) hrefs.add(href);
                });
                return Array.from(hrefs).slice(0, 100);
            }
        """)

        return PageMetadata(
            title=title,
            meta_description=meta_desc or "",
            h1s=h1s or [],
            links=links or [],
            status_code=status_code,
        )

    except Exception as exc:
        logger.warning("Metadata extraction failed: %s", exc)
        return PageMetadata(status_code=status_code, is_partial=True, error=str(exc))


def _extract_dom(page: Page) -> str:
    """Extract the DOM HTML, capped at MAX_DOM_NODES elements.

    Returns the full HTML if under the cap, otherwise a truncated version
    with a marker comment indicating truncation.
    """
    try:
        node_count = page.evaluate("() => document.querySelectorAll('*').length")

        if node_count <= MAX_DOM_NODES:
            return page.content()

        # Truncated extraction — get only the most important elements
        logger.info("DOM has %d nodes (cap=%d), extracting truncated version", node_count, MAX_DOM_NODES)
        truncated_html = page.evaluate(f"""
            () => {{
                const allNodes = document.querySelectorAll('*');
                const keep = {MAX_DOM_NODES};
                // Remove nodes beyond the cap from a cloned document
                const clone = document.documentElement.cloneNode(true);
                const cloneNodes = clone.querySelectorAll('*');
                for (let i = keep; i < cloneNodes.length; i++) {{
                    cloneNodes[i].remove();
                }}
                return '<!-- Optilens: DOM truncated at {MAX_DOM_NODES} nodes (original: ' + allNodes.length + ') -->\\n' + clone.outerHTML;
            }}
        """)
        return truncated_html

    except Exception as exc:
        logger.warning("DOM extraction failed: %s", exc)
        # Fallback — try page.content() without the node check
        try:
            return page.content()
        except Exception:
            return f"<!-- DOM extraction failed: {exc} -->"


def _is_behind_auth(page: Page) -> bool:
    """Heuristic check for login/auth walls.

    Returns True if the page likely requires authentication to view content.
    """
    try:
        return page.evaluate("""
            () => {
                const html = document.body ? document.body.innerText.toLowerCase() : '';
                const hasLoginForm = document.querySelector('form[action*="login"], form[action*="signin"], input[type="password"]') !== null;
                const hasAuthText = /sign in|log in|access denied|unauthorized|403 forbidden/.test(html);
                return hasLoginForm && hasAuthText;
            }
        """)
    except Exception:
        return False


def _metadata_to_dict(meta: PageMetadata) -> dict:
    """Convert PageMetadata dataclass to a plain dict for JSON serialization."""
    return {
        "title": meta.title,
        "meta_description": meta.meta_description,
        "h1s": meta.h1s,
        "links": meta.links,
        "status_code": meta.status_code,
        "is_partial": meta.is_partial,
        "error": meta.error,
    }
