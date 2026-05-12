"""QR code generation.

Thin wrapper around the ``qrcode`` library so the ORS tool and the scripts
in this repo share one rendering path. Error-correction level Q (~25%)
balances size vs. print-durability for pack-list labels.
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_Q

logger = logging.getLogger(__name__)


def render_qr_png(url: str, out_path: Path, box_size: int = 8, border: int = 2) -> Path:
    """Render ``url`` as a PNG QR code to ``out_path``.

    Args:
        url: Target URL to encode.
        out_path: Destination PNG path; parent dirs are created.
        box_size: Pixels per QR module. 8 is a good default for 1-inch labels.
        border: Quiet-zone in modules. Keep >= 2 per the spec.

    Returns:
        The path written (same as ``out_path``).
    """
    if not url:
        raise ValueError("render_qr_png: url must be non-empty")
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_Q,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    logger.info("Wrote QR code for %s to %s", url, out_path)
    return out_path


def render_qr_bytes(url: str, box_size: int = 8, border: int = 2) -> bytes:
    """Return a QR PNG as bytes, for callers embedding directly in a PDF."""
    if not url:
        raise ValueError("render_qr_bytes: url must be non-empty")
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_Q,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
