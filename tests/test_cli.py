"""Tests for the bbi-compliance CLI (audit, publish-index, publish-items, url)."""
from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from banfieldbio_compliance.cli import cli


def test_audit_passes_on_a_clean_repo(tmp_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "audit"])
    assert result.exit_code == 0, result.output


def test_audit_fails_on_an_sds_pdf_that_never_passed_the_gate(tmp_repo: Path) -> None:
    """Dropping a PDF into docs/sds/ used to be enough to publish it. Now it
    is a finding: the only way in is `ors publish-item`."""
    (tmp_repo / "docs" / "sds" / "C1174.pdf").write_bytes(b"%PDF-1.4\n%stub\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "audit"])
    assert result.exit_code == 1
    assert "orphan SDS PDF" in result.output


def test_audit_fails_on_a_stale_item_page(tmp_repo: Path) -> None:
    """An item page for something no longer in the index stays live on Pages
    until the directory is deleted."""
    (tmp_repo / "docs" / "item" / "C9999").mkdir(parents=True)
    (tmp_repo / "docs" / "item" / "C9999" / "index.html").write_text("<p>x</p>")
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "audit"])
    assert result.exit_code == 1
    assert "stale item page" in result.output


def test_audit_ignores_an_empty_item_directory(tmp_repo: Path) -> None:
    """Deleting a page on Windows/OneDrive often leaves the directory behind.
    It serves nothing and git does not track it, so flagging it would fail a
    local audit while CI passes -- and a check that cries wolf gets ignored."""
    (tmp_repo / "docs" / "item" / "C9999").mkdir(parents=True)
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "audit"])
    assert result.exit_code == 0, result.output


def test_audit_fails_on_a_shipment_artifact(tmp_repo: Path) -> None:
    """The Stage 0 exposure, caught in CI if it ever comes back."""
    ship = tmp_repo / "docs" / "shipment"
    ship.mkdir(parents=True, exist_ok=True)
    (ship / "deadbeef.pdf").write_bytes(b"%PDF-1.4\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "audit"])
    assert result.exit_code == 1
    assert "shipment artifact" in result.output


def test_audit_fails_on_a_non_public_index_entry(tmp_repo: Path) -> None:
    (tmp_repo / "data" / "index.json").write_text(
        '[{"inv_num": "P2001", "name": "BB-Lure 7", "disclosure": "redacted",'
        ' "source_url": "https://example.invalid/x"}]',
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "audit"])
    assert result.exit_code == 1
    assert "not public" in result.output


def test_scan_mirrors_command_is_gone(tmp_repo: Path) -> None:
    """It was a default-allow path into a public repo. Removed, not fixed."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "scan-mirrors"])
    assert result.exit_code != 0


def test_publish_index_writes_docs_index_html(tmp_repo: Path) -> None:
    (tmp_repo / "data" / "index.json").write_text(
        '[{"inv_num": "C1174", "name": "Kraton", "disclosure": "public",'
        ' "mirror_path": "sds/C1174.pdf"}]',
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo-root", str(tmp_repo), "publish-index"])
    assert result.exit_code == 0, result.output
    html = (tmp_repo / "docs" / "index.html").read_text(encoding="utf-8")
    assert "C1174" in html and "Kraton" in html


def test_url_command_resolves_mirror(tmp_repo: Path) -> None:
    (tmp_repo / "data" / "index.json").write_text(
        '[{"inv_num": "C1174", "name": "Kraton", "disclosure": "public",'
        ' "mirror_path": "sds/C1174.pdf"}]',
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
