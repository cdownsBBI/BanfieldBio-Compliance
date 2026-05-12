"""Tests for QR code generation — verifies output is a valid PNG, not the contents."""
from __future__ import annotations

from pathlib import Path

import pytest

from banfieldbio_compliance.qr import render_qr_bytes, render_qr_png


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def test_render_qr_png_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "qr.png"
    render_qr_png("https://example.com/shipment/abc.pdf", out)
    data = out.read_bytes()
    assert data[:8] == _PNG_MAGIC
    assert len(data) > 200  # QR PNGs are at least a few hundred bytes


def test_render_qr_bytes_returns_png() -> None:
    data = render_qr_bytes("https://example.com/shipment/abc.pdf")
    assert data[:8] == _PNG_MAGIC


def test_render_qr_rejects_empty_url(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        render_qr_png("", tmp_path / "q.png")
    with pytest.raises(ValueError):
        render_qr_bytes("")
