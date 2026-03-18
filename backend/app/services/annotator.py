"""Pillow screenshot annotation service.

Draws colored bounding boxes, arrow callouts, and issue numbers on
screenshots to highlight detected problems. Severity-coded using
Optilens brand colors. Annotated images are uploaded to Supabase Storage
and served via signed URLs.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("optilens.services.annotator")

# Severity -> color mapping (brand colors)
SEVERITY_COLORS = {
    "critical": (255, 77, 106),    # #FF4D6A red
    "high": (255, 84, 1),          # #FF5401 burnt orange
    "medium": (245, 158, 11),      # #F59E0B amber
    "low": (79, 142, 255),         # #4F8EFF blue/info
}

# Default box color for unknown severity
DEFAULT_COLOR = (136, 136, 136)     # #888888 grey

# Annotation styling
BOX_LINE_WIDTH = 3
LABEL_PADDING = 4
LABEL_FONT_SIZE = 14
ARROW_LENGTH = 30


def annotate_screenshot(
    screenshot_b64: str,
    issues: Sequence[dict],
) -> str:
    """Draw annotation boxes and labels on a screenshot.

    Args:
        screenshot_b64: Base64-encoded PNG screenshot.
        issues: List of issue dicts, each with optional 'coordinates' dict
            containing {x, y, width, height} and 'severity' field.

    Returns:
        Base64-encoded annotated PNG.
    """
    # Decode screenshot
    img_bytes = base64.b64decode(screenshot_b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    # Create overlay for semi-transparent boxes
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Try to load a font — fall back to default if unavailable
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", LABEL_FONT_SIZE)
    except (OSError, IOError):
        font = ImageFont.load_default()

    issue_number = 0
    for issue in issues:
        coords = issue.get("coordinates")
        if not coords:
            continue

        issue_number += 1
        severity = issue.get("severity", "medium")
        color = SEVERITY_COLORS.get(severity, DEFAULT_COLOR)
        color_with_alpha = color + (60,)  # Semi-transparent fill

        x = int(coords.get("x", 0))
        y = int(coords.get("y", 0))
        w = int(coords.get("width", 100))
        h = int(coords.get("height", 50))

        # Clamp coordinates to image bounds
        x = max(0, min(x, img.width - 10))
        y = max(0, min(y, img.height - 10))
        w = min(w, img.width - x)
        h = min(h, img.height - y)

        # Draw semi-transparent filled rectangle
        draw.rectangle([x, y, x + w, y + h], fill=color_with_alpha)

        # Draw solid border
        draw.rectangle([x, y, x + w, y + h], outline=color, width=BOX_LINE_WIDTH)

        # Draw issue number label
        label = f"#{issue_number}"
        _draw_label(draw, label, x, y, color, font)

        # Draw arrow callout pointing to the top-left of the box
        _draw_arrow(draw, x, y, color)

    # Composite overlay onto original
    annotated = Image.alpha_composite(img, overlay)

    # Convert back to base64 PNG
    output = io.BytesIO()
    annotated.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)

    return base64.b64encode(output.read()).decode("utf-8")


def annotate_and_upload(
    screenshot_b64: str,
    issues: Sequence[dict],
    audit_id: str,
    page_url: str,
) -> str | None:
    """Annotate a screenshot and upload it to Supabase Storage.

    Returns the storage path (for signed URL generation), or None on failure.
    """
    # Only annotate issues with critical or high severity
    annotatable = [i for i in issues if i.get("severity") in ("critical", "high") and i.get("coordinates")]
    if not annotatable:
        return None

    try:
        annotated_b64 = annotate_screenshot(screenshot_b64, annotatable)

        from app.db.supabase import get_supabase_client
        supabase = get_supabase_client()

        # Generate a clean filename from the page URL
        from urllib.parse import urlparse
        parsed = urlparse(page_url)
        path_slug = parsed.path.strip("/").replace("/", "_") or "index"
        file_name = f"{audit_id}/{path_slug}_annotated.png"

        img_bytes = base64.b64decode(annotated_b64)

        supabase.storage.from_("screenshots").upload(
            file_name,
            img_bytes,
            {"content-type": "image/png"},
        )

        logger.info("Annotated screenshot uploaded: %s", file_name)
        return file_name

    except Exception as exc:
        logger.error("Annotation upload failed: %s", exc, exc_info=True)
        return None


def get_signed_url(storage_path: str, expires_in: int = 7776000) -> str | None:
    """Generate a signed URL for an annotated screenshot.

    Args:
        storage_path: Path in the screenshots bucket.
        expires_in: URL validity in seconds (default 90 days).

    Returns signed URL string or None on failure.
    """
    try:
        from app.db.supabase import get_supabase_client
        supabase = get_supabase_client()
        result = supabase.storage.from_("screenshots").create_signed_url(storage_path, expires_in)
        return result.get("signedURL")
    except Exception as exc:
        logger.error("Signed URL generation failed: %s", exc)
        return None


def _draw_label(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    color: tuple,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Draw a colored label badge above a bounding box."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Position label above the box
    label_x = x
    label_y = max(0, y - text_h - LABEL_PADDING * 2 - 2)

    # Draw label background
    draw.rectangle(
        [label_x, label_y, label_x + text_w + LABEL_PADDING * 2, label_y + text_h + LABEL_PADDING * 2],
        fill=color + (220,),
    )

    # Draw label text (white)
    draw.text(
        (label_x + LABEL_PADDING, label_y + LABEL_PADDING),
        text,
        fill=(255, 255, 255, 255),
        font=font,
    )


def _draw_arrow(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple) -> None:
    """Draw a small arrow callout pointing toward the annotated area."""
    # Arrow from upper-left, pointing down-right into the box
    start_x = max(0, x - ARROW_LENGTH)
    start_y = max(0, y - ARROW_LENGTH)

    draw.line(
        [(start_x, start_y), (x, y)],
        fill=color + (200,),
        width=2,
    )

    # Arrowhead
    draw.polygon(
        [(x, y), (x - 6, y - 10), (x + 4, y - 8)],
        fill=color + (200,),
    )
