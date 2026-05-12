"""Tests for URL construction and hybrid SDS resolution.

Token values are generated via ``uuid.uuid4()`` rather than hardcoded as
string literals so gitleaks' ``generic-api-key`` heuristic doesn't false-
positive on what would otherwise look like a leaked secret.
"""
from __future__ import annotations

import uuid

from banfieldbio_compliance.config import SiteConfig
from banfieldbio_compliance.index import SdsEntry
from banfieldbio_compliance.urls import (
    item_url,
    library_index_url,
    sds_url,
    shipment_pdf_url,
)


def test_item_url_uppercases(site_config: SiteConfig) -> None:
    assert item_url(site_config, "c1174") == (
        "https://cdownsBBI.github.io/BanfieldBio-Compliance/item/C1174/"
    )


def test_library_index_url(site_config: SiteConfig) -> None:
    assert library_index_url(site_config) == (
        "https://cdownsBBI.github.io/BanfieldBio-Compliance/"
    )


def test_shipment_pdf_url_uses_token(site_config: SiteConfig) -> None:
    token = str(uuid.uuid4())
    assert shipment_pdf_url(site_config, token) == (
        f"https://cdownsBBI.github.io/BanfieldBio-Compliance/shipment/{token}.pdf"
    )


def test_sds_url_prefers_mirror(
    site_config: SiteConfig, entry_with_mirror: SdsEntry
) -> None:
    # Mirror present AND source URL present -- mirror wins.
    url = sds_url(site_config, entry_with_mirror)
    assert url == "https://cdownsBBI.github.io/BanfieldBio-Compliance/sds/C1174.pdf"


def test_sds_url_falls_back_to_source(
    site_config: SiteConfig, entry_link_only: SdsEntry
) -> None:
    url = sds_url(site_config, entry_link_only)
    assert url == "https://sigmaaldrich.example/sds/DEP.pdf"


def test_sds_url_returns_none_when_no_sources(
    site_config: SiteConfig, entry_no_sds: SdsEntry
) -> None:
    assert sds_url(site_config, entry_no_sds) is None


def test_sds_url_strips_leading_slash_in_mirror_path(site_config: SiteConfig) -> None:
    entry = SdsEntry(inv_num="C1", name="x", mirror_path="/sds/C1.pdf")
    url = sds_url(site_config, entry)
    assert url == "https://cdownsBBI.github.io/BanfieldBio-Compliance/sds/C1.pdf"


def test_urls_swap_cleanly_to_custom_domain(
    custom_domain_config: SiteConfig, entry_with_mirror: SdsEntry
) -> None:
    # Verifies path shape is identical under a custom domain -- so already-
    # printed QR codes keep working after a domain move.
    token = str(uuid.uuid4())
    assert shipment_pdf_url(custom_domain_config, token) == (
        f"https://compliance.banfieldbio.com/shipment/{token}.pdf"
    )
    assert sds_url(custom_domain_config, entry_with_mirror) == (
        "https://compliance.banfieldbio.com/sds/C1174.pdf"
    )
