"""Tests for SDS index load/save round-trips."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from banfieldbio_compliance.index import SdsEntry, SdsIndex, load_index, save_index


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    idx = load_index(tmp_path / "nope.json")
    assert idx.entries == []


def test_round_trip(tmp_path: Path, sample_index: SdsIndex) -> None:
    path = tmp_path / "index.json"
    save_index(sample_index, path)
    loaded = load_index(path)
    assert {e.inv_num for e in loaded.entries} == {"C1174", "C1025", "C9999"}
    c1174 = loaded.by_inv_num("C1174")
    assert c1174 and c1174.manufacturer == "Kraton Corporation"


def test_saved_index_is_sorted_and_pretty(tmp_path: Path, sample_index: SdsIndex) -> None:
    path = tmp_path / "index.json"
    save_index(sample_index, path)
    text = path.read_text(encoding="utf-8")
    # Indented JSON so the file diffs cleanly in PRs.
    assert '"inv_num": "C1025"' in text
    lines = text.splitlines()
    inv_line_order = [i for i, line in enumerate(lines) if '"inv_num"' in line]
    assert len(inv_line_order) == 3
    # Entries sorted: C1025, C1174, C9999 — first should be C1025.
    first_inv = json.loads(text)[0]["inv_num"]
    assert first_inv == "C1025"


def test_load_accepts_bare_list(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    path.write_text('[{"inv_num": "C1", "name": "x"}]', encoding="utf-8")
    idx = load_index(path)
    assert idx.entries[0].inv_num == "C1"


def test_load_accepts_entries_object(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    path.write_text(
        '{"entries": [{"inv_num": "C1", "name": "x"}]}', encoding="utf-8"
    )
    idx = load_index(path)
    assert idx.entries[0].inv_num == "C1"


def test_load_rejects_invalid_top_level(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    path.write_text('"not a list"', encoding="utf-8")
    with pytest.raises(ValueError, match="entries"):
        load_index(path)


def test_by_inv_num_case_insensitive(sample_index: SdsIndex) -> None:
    assert sample_index.by_inv_num("c1174") is not None
    assert sample_index.by_inv_num("C1174") is not None
    assert sample_index.by_inv_num("c99") is None


def test_entry_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        SdsEntry(inv_num="C1", name="x", bogus="y")  # type: ignore[call-arg]


def test_entry_has_mirror_flag() -> None:
    e = SdsEntry(inv_num="C1", name="x", mirror_path="sds/C1.pdf")
    assert e.has_mirror and not e.has_source_link
    e2 = SdsEntry(inv_num="C2", name="x", source_url="https://e/")
    assert e2.has_source_link and not e2.has_mirror
