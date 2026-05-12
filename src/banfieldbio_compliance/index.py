"""SDS index — the map from Inv# to {mirror_path, source_url, metadata}.

Stored on disk as ``data/index.json`` (list of entries). Hybrid hosting means
each entry can have a ``mirror_path`` (relative to the Pages root) pointing to
a locally-mirrored PDF, a ``source_url`` pointing to the manufacturer's own
hosted SDS, or both. Resolvers prefer the mirror when present and fall back
to the source URL.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class SdsEntry(BaseModel):
    """One item's SDS metadata."""

    model_config = ConfigDict(extra="forbid")

    inv_num: str = Field(..., description="Primary key; matches the lab Inv# (e.g., C1174).")
    name: str
    cas_num: str | None = None
    manufacturer: str | None = None
    mirror_path: str | None = Field(
        default=None,
        description="Path to mirrored PDF relative to Pages root, e.g. 'sds/C1174.pdf'.",
    )
    source_url: str | None = Field(
        default=None,
        description="Manufacturer's own SDS URL. Used as fallback when mirror is absent.",
    )
    sds_version: str | None = None
    added_on: date | None = None

    @property
    def has_mirror(self) -> bool:
        return bool(self.mirror_path)

    @property
    def has_source_link(self) -> bool:
        return bool(self.source_url)


class SdsIndex(BaseModel):
    """Collection of SDS entries keyed by Inv#."""

    model_config = ConfigDict(extra="forbid")

    entries: list[SdsEntry] = Field(default_factory=list)

    def by_inv_num(self, inv_num: str) -> SdsEntry | None:
        key = inv_num.strip().upper()
        for entry in self.entries:
            if entry.inv_num.upper() == key:
                return entry
        return None

    def sorted_by_inv_num(self) -> list[SdsEntry]:
        return sorted(self.entries, key=lambda e: e.inv_num.upper())


def load_index(index_path: Path) -> SdsIndex:
    """Load the SDS index from JSON.

    An empty or missing file returns an empty index rather than erroring; the
    typical workflow is to bootstrap the library from zero entries.
    """
    if not index_path.exists():
        logger.info("Index file %s not found, starting empty", index_path)
        return SdsIndex()
    raw = json.loads(index_path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        entries = raw
    elif isinstance(raw, dict) and "entries" in raw:
        entries = raw["entries"]
    else:
        raise ValueError(
            f"Index {index_path} must be a list of entries or an object with 'entries'."
        )
    return SdsIndex(entries=[SdsEntry(**e) for e in entries])


def save_index(index: SdsIndex, index_path: Path) -> None:
    """Write the index to disk as a plain JSON list for diff-friendliness."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        e.model_dump(mode="json", exclude_none=True) for e in index.sorted_by_inv_num()
    ]
    index_path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    logger.info("Wrote %d entries to %s", len(payload), index_path)
