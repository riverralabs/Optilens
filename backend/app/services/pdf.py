"""WeasyPrint PDF generation service.

Full implementation in Step 1.8.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("optilens.services.pdf")


def generate_audit_pdf(audit: dict) -> str:
    """Generate a branded PDF report for an audit.

    Returns the storage path of the uploaded PDF.
    Full implementation in Step 1.8.
    """
    raise NotImplementedError("PDF generation not yet implemented. Build in Step 1.8.")
