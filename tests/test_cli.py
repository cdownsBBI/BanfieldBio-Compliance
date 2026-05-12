"""Tests for the bbi-compliance CLI (scan-mirrors, publish-index, url)."""
from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from banfieldbio_compliance.cli import cli


def test_scan_mirrors_adds_new_entries(tmp_repo: Path) -> None:
    # Drop two PDFs into docs/sds/ and confirm the index grows.
    (tmp_repo / "docs" / "sds" / "C1174.pdf").write_bytes(b"%PDF-1.4\n%stub\n")
    (tmp_repo / "docs" / "sds" / "C1025.pdf").write_bytes(b"%PDF-1.4\n%stub\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "scan-mirrors"])
    assert result.exit_code == 0, result.output
    data = json.loads((tmp_repo / "data" / "index.json").read_text(encoding="utf-8"))
    inv = {e["inv_num"] for e in data}
    assert inv == {"C1174", "C1025"}


def test_scan_mirrors_is_idempotent(tmp_repo: Path) -> None:
    (tmp_repo / "docs" / "sds" / "C1174.pdf").write_bytes(b"%PDF-1.4\n")
    runner = CliRunner()
    runner.invoke(cli, ["--repo-root", str(tmp_repo), "scan-mirrors"])
    # Run again — should not duplicate.
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "scan-mirrors"])
    assert result.exit_code == 0
    data = json.loads((tmp_repo / "data" / "index.json").read_text(encoding="utf-8"))
    assert len(data) == 1


def test_publish_index_writes_docs_index_html(tmp_repo: Path) -> None:
    (tmp_repo / "data" / "index.json").write_text(
        '[{"inv_num": "C1174", "name": "Kraton", "mirror_path": "sds/C1174.pdf"}]',
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "publish-index"])
    assert result.exit_code == 0, result.output
    html = (tmp_repo / "docs" / "index.html").read_text(encoding="utf-8")
    assert "C1174" in html and "Kraton" in html


def test_url_command_resolves_mirror(tmp_repo: Path) -> None:
    (tmp_repo / "data" / "index.json").write_text(
        '[{"inv_num": "C1174", "name": "Kraton", "mirror_path": "sds/C1174.pdf"}]',
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "url", "C1174"])
    assert result.exit_code == 0
    assert result.output.strip() == (
        "https://cdownsBBI.github.io/BanfieldBio-Compliance/sds/C1174.pdf"
    )


def test_url_command_errors_for_unknown_inv(tmp_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "url", "C9999"])
    assert result.exit_code == 2
