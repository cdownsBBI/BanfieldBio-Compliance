"""URL construction for the public Pages site.

All URLs are absolute and rooted at ``SiteConfig.base_url``. Hybrid
resolution for SDS links: prefer the mirrored PDF when the index entry has
one, otherwise fall back to the manufacturer's ``source_url``. Return
``None`` when neither exists so callers can choose to show a "no SDS on
file" state instead of a broken link.

Per-shipment URLs are NOT constructed here, and no longer can be. Shipment
PDFs are not part of this site: they carry ship dates, quantities, lot
numbers and CAS, and are served from the gated endpoint instead. A helper
that composed a public shipment URL used to live in this module; it was
removed because the only thing it could produce was a URL that must not
exist. This module covers the public, intentionally-enumerable surface
only (item, library, sds).
"""

from __future__ import annotations

from banfieldbio_compliance.config import SiteConfig
from banfieldbio_compliance.index import SdsEntry


def item_url(config: SiteConfig, inv_num: str) -> str:
    """URL of the per-item landing page (info + SDS button).

    Per-item pages are the stable indirection layer: SDS links inside any
    per-shipment PDF should point here, NOT directly to a manufacturer URL,
    so that link-rot in `data/index.json` can be repaired in one place.
    """
    return f"{config.base_url}/{config.item_dir}/{inv_num.upper()}/"


def sds_url(config: SiteConfig, entry: SdsEntry) -> str | None:
    """Resolve an entry to its SDS link under hybrid rules.

    Returns:
        Mirrored PDF URL if ``entry.mirror_path`` is set. Otherwise the
        manufacturer's ``source_url``. ``None`` if neither is available.
    """
    if entry.has_mirror:
        assert entry.mirror_path is not None  # for type-checkers
        path = entry.mirror_path.lstrip("/")
        return f"{config.base_url}/{path}"
    if entry.has_source_link:
        return entry.source_url
    return None


def library_index_url(config: SiteConfig) -> str:
    """Top-level library landing page."""
    return f"{config.base_url}/"

