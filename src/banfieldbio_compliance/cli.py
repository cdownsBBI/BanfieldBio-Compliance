"""Command-line interface for this repo.

    bbi-compliance audit           # verify nothing unpublishable is in the tree
    bbi-compliance publish-index   # regenerate docs/index.html (library home)
    bbi-compliance publish-items   # regenerate per-item pages for every entry
    bbi-compliance url <INV#>      # print the SDS URL an entry resolves to

This CLI does not decide what may be published and cannot add an entry.
``data/index.json`` is written only by the private ORS tool
(``ors publish-item``), which reads each item's disclosure policy from the
inventory DB and refuses anything not explicitly public. The commands here
render the site from that index and audit the result.

``scan-mirrors`` used to add an index entry for any PDF dropped into
docs/sds/. That was a default-allow path into a public repo -- and by the
time it ran, the PDF was already committed. It is gone; ``audit`` reports
such files as orphans instead.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click
from pydantic import ValidationError

from banfieldbio_compliance.config import SiteConfig, load_config
from banfieldbio_compliance.index import load_index
from banfieldbio_compliance.landing import render_item_page, render_library_index
from banfieldbio_compliance.urls import sds_url

logger = logging.getLogger("banfieldbio_compliance")

DEFAULT_REPO_ROOT = Path(".")


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _paths(repo_root: Path) -> tuple[SiteConfig, Path, Path]:
    """Load config and return (config, index_path, docs_root)."""
    config = load_config(repo_root / "config.toml")
    index_path = repo_root / config.index_file
    docs_root = repo_root / "docs"
    return config, index_path, docs_root


@click.group()
@click.option("--verbose", "-v", is_flag=True)
@click.option("--repo-root", type=click.Path(path_type=Path), default=DEFAULT_REPO_ROOT,
              show_default=True, help="Root of the BanfieldBio-Compliance repo.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, repo_root: Path) -> None:
    """BanfieldBio-Compliance maintenance commands."""
    _setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["repo_root"] = repo_root.resolve()


@cli.command("audit")
@click.pass_context
def audit(ctx: click.Context) -> None:
    """Verify the repo contains nothing that must not be public.

    Four checks, any of which fails the build:

    1. Every index entry declares ``disclosure: "public"``. Enforced by the
       schema, so a bad index fails to load at all.
    2. No orphan PDFs in docs/sds/ -- a file with no index entry got there
       without passing the ORS gate.
    3. No orphan per-item pages -- a stale page for an item that has since
       been unpublished stays live on Pages until it is deleted.
    4. docs/shipment/ holds no files. Shipment artifacts belong on the
       gated endpoint and are permanent once committed here.

    Exits non-zero on any finding, so CI blocks the push.
    """
    repo_root = ctx.obj["repo_root"]
    try:
        config, index_path, docs_root = _paths(repo_root)
        index = load_index(index_path)
    except ValidationError as e:
        click.echo(
            "FAIL: data/index.json contains an entry that is not public, or is "
            "missing its disclosure field. The index is a public surface; only "
            "items classified public in the ORS inventory belong in it.",
            err=True,
        )
        click.echo(str(e), err=True)
        sys.exit(1)

    findings: list[str] = []
    known = {e.inv_num.upper() for e in index.entries}

    sds_dir = docs_root / config.sds_dir
    if sds_dir.exists():
        orphan_pdfs = sorted(
            pdf.name for pdf in sds_dir.glob("*.pdf") if pdf.stem.upper() not in known
        )
        findings += [
            f"orphan SDS PDF with no index entry: {config.sds_dir}/{name} "
            f"(publish it via `ors publish-item`, or delete it)"
            for name in orphan_pdfs
        ]

    item_dir = docs_root / config.item_dir
    if item_dir.exists():
        orphan_pages = sorted(
            d.name
            for d in item_dir.iterdir()
            # An EMPTY directory is not a published page: Pages serves nothing
            # from it and git does not track it. Windows/OneDrive routinely
            # leaves such shells behind after a delete, and flagging them would
            # make a local audit fail while CI (a fresh checkout) passes --
            # which is how people learn to ignore the audit.
            if d.is_dir() and any(d.iterdir()) and d.name.upper() not in known
        )
        findings += [
            f"stale item page for an unpublished item: {config.item_dir}/{name}/ "
            f"(still live on Pages; delete the directory)"
            for name in orphan_pages
        ]

    shipment_dir = docs_root / "shipment"
    if shipment_dir.exists():
        stray = sorted(f.name for f in shipment_dir.rglob("*") if f.is_file())
        findings += [
            f"shipment artifact in the public repo: shipment/{name} "
            f"(these belong on the gated endpoint and are permanent once committed)"
            for name in stray
        ]

    for f in findings:
        click.echo(f"FAIL: {f}", err=True)
    if findings:
        click.echo(f"{len(findings)} finding(s)", err=True)
        sys.exit(1)
    click.echo(f"OK: {len(index.entries)} public entries, no findings")


@cli.command("publish-index")
@click.pass_context
def publish_index(ctx: click.Context) -> None:
    """Regenerate docs/index.html from data/index.json."""
    config, index_path, docs_root = _paths(ctx.obj["repo_root"])
    index = load_index(index_path)
    dest = render_library_index(config, index, docs_root)
    click.echo(f"Wrote {dest} ({len(index.entries)} items)")


@cli.command("publish-items")
@click.pass_context
def publish_items(ctx: click.Context) -> None:
    """Regenerate per-item landing pages for every entry in the index."""
    config, index_path, docs_root = _paths(ctx.obj["repo_root"])
    index = load_index(index_path)
    for entry in index.entries:
        render_item_page(config, entry, docs_root)
    click.echo(f"Wrote {len(index.entries)} item pages")


@cli.command("url")
@click.argument("inv_num")
@click.pass_context
def url_cmd(ctx: click.Context, inv_num: str) -> None:
    """Resolve and print the SDS URL for an Inv#."""
    config, index_path, _ = _paths(ctx.obj["repo_root"])
    index = load_index(index_path)
    entry = index.by_inv_num(inv_num)
    if entry is None:
        click.echo(f"Inv# {inv_num} not in index.", err=True)
        sys.exit(2)
    link = sds_url(config, entry)
    if link is None:
        click.echo(f"Inv# {inv_num}: no SDS on file (neither mirror nor source URL).", err=True)
        sys.exit(2)
    click.echo(link)


if __name__ == "__main__":  # pragma: no cover
    cli()
