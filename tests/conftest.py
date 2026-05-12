"""Shared pytest fixtures for banfieldbio_compliance."""
from __future__ import annotations

from pathlib import Path

import pytest

from banfieldbio_compliance.config import SiteConfig
from banfieldbio_compliance.index import SdsEntry, SdsIndex


@pytest.fixture()
def site_config() -> SiteConfig:
    """A fully-populated config with a github.io base URL."""
    return SiteConfig(
        github_user="cdownsBBI",
        repo_name="BanfieldBio-Compliance",
        custom_domain="",
        sds_dir="sds",
        shipment_dir="shipment",
        item_dir="item",
        index_file="data/index.json",
    )


@pytest.fixture()
def custom_domain_config() -> SiteConfig:
    """Same config but with a custom domain override."""
    return SiteConfig(
        github_user="cdownsBBI",
        repo_name="BanfieldBio-Compliance",
        custom_domain="https://compliance.banfieldbio.com",
        sds_dir="sds",
        shipment_dir="shipment",
        item_dir="item",
        index_file="data/index.json",
    )


@pytest.fixture()
def entry_with_mirror() -> SdsEntry:
    return SdsEntry(
        inv_num="C1174",
        name="Kraton G 1730",
        cas_num="68648-89-5",
        manufacturer="Kraton Corporation",
        mirror_path="sds/C1174.pdf",
        source_url="https://kraton.example/sds/G1730.pdf",
    )


@pytest.fixture()
def entry_link_only() -> SdsEntry:
    return SdsEntry(
        inv_num="C1025",
        name="Diethyl phthalate",
        cas_num="84-66-2",
        manufacturer="Sigma-Aldrich",
        mirror_path=None,
        source_url="https://sigmaaldrich.example/sds/DEP.pdf",
    )


@pytest.fixture()
def entry_no_sds() -> SdsEntry:
    return SdsEntry(
        inv_num="C9999",
        name="Unknown compound",
        cas_num=None,
        mirror_path=None,
        source_url=None,
    )


@pytest.fixture()
def sample_index(
    entry_with_mirror: SdsEntry,
    entry_link_only: SdsEntry,
    entry_no_sds: SdsEntry,
) -> SdsIndex:
    return SdsIndex(entries=[entry_with_mirror, entry_link_only, entry_no_sds])


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    """Lay out a minimal repo structure for scripts/CLI tests."""
    (tmp_path / "docs" / "sds").mkdir(parents=True)
    (tmp_path / "docs" / "shipment").mkdir(parents=True)
    (tmp_path / "docs" / "item").mkdir(parents=True)
    (tmp_path / "docs" / "assets").mkdir(parents=True)
    (tmp_path / "data").mkdir(parents=True)
    (tmp_path / "data" / "index.json").write_text("[]", encoding="utf-8")
    (tmp_path / "config.toml").write_text(
        '[site]\n'
        'github_user = "cdownsBBI"\n'
        'repo_name = "BanfieldBio-Compliance"\n'
        'custom_domain = ""\n'
        '\n'
        '[library]\n'
        'sds_dir = "sds"\n'
        'shipment_dir = "shipment"\n'
        'item_dir = "item"\n'
        'index_file = "data/index.json"\n',
        encoding="utf-8",
    )
    return tmp_path
