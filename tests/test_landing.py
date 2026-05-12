"""Tests for landing page generation.

Per-shipment HTML rendering was removed when the architecture switched to
opaque-token per-shipment PDFs (those PDFs are rendered by the private ORS
publisher, not this library). Only per-item pages and the library index
are rendered here.
"""
from __future__ import annotations

from pathlib import Path

from banfieldbio_compliance.config import SiteConfig
from banfieldbio_compliance.index import SdsEntry, SdsIndex
from banfieldbio_compliance.landing import render_item_page, render_library_index


def test_render_item_page(
    site_config: SiteConfig, entry_with_mirror: SdsEntry, tmp_path: Path
) -> None:
    dest = render_item_page(site_config, entry_with_mirror, tmp_path / "docs")
    html = dest.read_text(encoding="utf-8")
    assert "C1174" in html
    assert "Kraton G 1730" in html
    assert "68648-89-5" in html
    assert (
        'href="https://cdownsBBI.github.io/BanfieldBio-Compliance/sds/C1174.pdf"'
        in html
    )


def test_render_item_page_link_only_marks_external(
    site_config: SiteConfig, entry_link_only: SdsEntry, tmp_path: Path
) -> None:
    dest = render_item_page(site_config, entry_link_only, tmp_path / "docs")
    html = dest.read_text(encoding="utf-8")
    # Source URL gets noopener + target=_blank when it's not a mirror.
    assert 'target="_blank"' in html
    assert "(external)" in html
    assert 'href="https://sigmaaldrich.example/sds/DEP.pdf"' in html


def test_render_item_page_no_sds_state(
    site_config: SiteConfig, entry_no_sds: SdsEntry, tmp_path: Path
) -> None:
    dest = render_item_page(site_config, entry_no_sds, tmp_path / "docs")
    html = dest.read_text(encoding="utf-8")
    assert "No SDS on file" in html


def test_render_item_page_escapes_html_in_names(
    site_config: SiteConfig, tmp_path: Path
) -> None:
    entry = SdsEntry(
        inv_num="C1",
        name="<script>alert(1)</script>",
        mirror_path="sds/C1.pdf",
    )
    dest = render_item_page(site_config, entry, tmp_path / "docs")
    html = dest.read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_library_index(
    site_config: SiteConfig, sample_index: SdsIndex, tmp_path: Path
) -> None:
    dest = render_library_index(site_config, sample_index, tmp_path / "docs")
    html = dest.read_text(encoding="utf-8")
    assert "Compliance Library" in html
    assert "3 item(s)" in html
    # Library rows link to item pages.
    assert "item/C1174" in html or "item/C1025" in html
    # Search input is present so the library page is filterable.
    assert 'id="q"' in html
