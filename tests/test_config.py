"""Tests for banfieldbio_compliance.config."""
from __future__ import annotations

from pathlib import Path

import pytest

from banfieldbio_compliance.config import SiteConfig, load_config


def test_base_url_from_github_user(site_config: SiteConfig) -> None:
    assert site_config.base_url == "https://cdownsBBI.github.io/BanfieldBio-Compliance"


def test_base_url_respects_custom_domain(custom_domain_config: SiteConfig) -> None:
    assert custom_domain_config.base_url == "https://compliance.banfieldbio.com"


def test_base_url_strips_trailing_slash_on_custom_domain() -> None:
    c = SiteConfig(
        github_user="x", repo_name="r",
        custom_domain="https://compliance.example.com/",
        sds_dir="sds", shipment_dir="shipment",
        item_dir="item", index_file="data/index.json",
    )
    assert c.base_url == "https://compliance.example.com"


def test_base_url_rejects_placeholder_user() -> None:
    c = SiteConfig(
        github_user="REPLACE_ME", repo_name="r", custom_domain="",
        sds_dir="sds", shipment_dir="shipment",
        item_dir="item", index_file="data/index.json",
    )
    with pytest.raises(ValueError, match="github_user"):
        _ = c.base_url


def test_load_config_reads_toml(tmp_repo: Path) -> None:
    cfg = load_config(tmp_repo / "config.toml")
    assert cfg.github_user == "cdownsBBI"
    assert cfg.sds_dir == "sds"
    assert cfg.index_file == "data/index.json"
