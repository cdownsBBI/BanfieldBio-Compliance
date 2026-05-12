"""Command-line interface for this repo.

    bbi-compliance scan-mirrors    # update index.json with any new PDFs in docs/sds/
    bbi-compliance publish-index   # regenerate docs/index.html (library home)
    bbi-compliance publish-items   # regenerate per-item pages for every entry
    bbi-compliance url <INV#>      # print the SDS URL an entry resolves to

The ORS private tool does its own per-shipment PDF publish — this CLI only
covers repo-level maintenance (item pages, library index, SDS mirroring).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from banfieldbio_compliance.config import SiteConfig, load_config
from banfieldbio_compliance.index import SdsEntry, load_index, save_index
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


@cli.command("scan-mirrors")
@click.pass_context
def scan_mirrors(ctx: click.Context) -> None:
    """Find new PDFs in docs/sds/ and add stub entries to the index.

    Filenames must match ``<INV#>.pdf`` (e.g., ``C1174.pdf``). For each new
    PDF, a minimal entry is added: name defaults to the Inv# and can be
    edited by hand afterward.
    """
    config, index_path, docs_root = _paths(ctx.obj["repo_root"])
    sds_dir = docs_root / config.sds_dir
    if not sds_dir.exists():
        click.echo(f"No {sds_dir} directory found.", err=True)
        sys.exit(1)
    index = load_index(index_path)
    known = {e.inv_num.upper() for e in index.entries}
    added: list[str] = []
    for pdf in sorted(sds_dir.glob("*.pdf")):
        inv_num = pdf.stem.upper()
        if inv_num in known:
            continue
        rel = f"{config.sds_dir}/{pdf.name}"
        index.entries.append(SdsEntry(inv_num=inv_num, name=inv_num, mirror_path=rel))
        added.append(inv_num)
    if added:
        save_index(index, index_path)
    click.echo(f"Added {len(added)} new entries: {', '.join(added) or '(none)'}")


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
