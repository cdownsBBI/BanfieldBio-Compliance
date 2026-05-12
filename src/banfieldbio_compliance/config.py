"""Site configuration loaded from ``config.toml``.

The config tells the library where the public site lives (github.io URL or a
custom domain) and which subdirectories the PDFs and landing pages use.
Downstream code always asks the config for a base URL; it never hardcodes it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as _toml
else:  # pragma: no cover
    import tomli as _toml  # type: ignore[no-redef]


@dataclass(frozen=True)
class SiteConfig:
    """Resolved site configuration.

    Attributes:
        github_user: GitHub username hosting the Pages site.
        repo_name: Name of the public repo (used in the github.io URL).
        custom_domain: Non-empty to override the derived github.io base URL.
        sds_dir: Subdir under Pages root containing mirrored PDFs.
        shipment_dir: Subdir under Pages root for per-shipment landing pages.
        item_dir: Subdir under Pages root for per-item landing pages.
        index_file: Path to the master index, relative to the repo root.
    """

    github_user: str
    repo_name: str
    custom_domain: str
    sds_dir: str
    shipment_dir: str
    item_dir: str
    index_file: str

    @property
    def base_url(self) -> str:
        """Absolute URL root for the Pages site, no trailing slash.

        Raises:
            ValueError: if neither ``custom_domain`` nor a valid ``github_user``
                is configured.
        """
        if self.custom_domain:
            return self.custom_domain.rstrip("/")
        if not self.github_user or self.github_user == "REPLACE_ME":
            raise ValueError(
                "config.toml: set [site].github_user or [site].custom_domain "
                "before constructing URLs."
            )
        return f"https://{self.github_user}.github.io/{self.repo_name}"


def load_config(config_path: Path) -> SiteConfig:
    """Load and validate ``config.toml``.

    Args:
        config_path: Path to the TOML file.

    Returns:
        A resolved ``SiteConfig``.

    Raises:
        FileNotFoundError: if the config file does not exist.
        KeyError: if required keys are missing.
    """
    with config_path.open("rb") as f:
        data = _toml.load(f)
    site = data.get("site", {})
    lib = data.get("library", {})
    return SiteConfig(
        github_user=str(site.get("github_user", "")).strip(),
        repo_name=str(site.get("repo_name", "BanfieldBio-Compliance")).strip(),
        custom_domain=str(site.get("custom_domain", "")).strip(),
        sds_dir=str(lib.get("sds_dir", "sds")).strip("/"),
        shipment_dir=str(lib.get("shipment_dir", "shipment")).strip("/"),
        item_dir=str(lib.get("item_dir", "item")).strip("/"),
        index_file=str(lib.get("index_file", "data/index.json")),
    )
