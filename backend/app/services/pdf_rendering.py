"""PDF rendering service.

Converts resume/cover letter HTML into PDF bytes using xhtml2pdf (pure Python,
no system dependencies). xhtml2pdf supports most CSS2/CSS3 used by our
templates; for advanced CSS (flexbox, complex grid) it gracefully degrades.
"""

import io
import logging

logger = logging.getLogger(__name__)


def render_html_to_pdf_bytes(html: str) -> io.BytesIO:
    """Convert an HTML string into a PDF byte stream.

    Returns a BytesIO buffer positioned at the start, suitable for sending as
    a streaming download response.
    """
    from xhtml2pdf import pisa

    buf = io.BytesIO()
    result = pisa.CreatePDF(
        src=html,
        dest=buf,
        encoding="utf-8",
        # xhtml2pdf emits "DEBUG: ..." warnings via logging; we keep them
        # but soften them so the application output isn't noisy.
        err=io.StringIO(),
    )

    if result.err:
        logger.warning("pdf_render_errors", extra={"count": result.err})
    buf.seek(0)
    return buf


def render_html_to_pdf(html: str) -> bytes:
    """Same as `render_html_to_pdf_bytes` but returns raw bytes."""
    return render_html_to_pdf_bytes(html).getvalue()
