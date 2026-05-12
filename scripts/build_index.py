"""Rescan docs/sds/ and merge any new PDFs into data/index.json.

Convenience wrapper equivalent to ``bbi-compliance scan-mirrors`` run from
the repo root. Useful for calling from an editor or automation script
without going through the Click entry point.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Make the src/ package importable when running this script directly.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from banfieldbio_compliance.config import load_config  # noqa: E402
from banfieldbio_compliance.index import SdsEntry, load_index, save_index  # noqa: E402


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
    config = load_config(ROOT / "config.toml")
    index_path = ROOT / config.index_file
    sds_dir = ROOT / "docs" / config.sds_dir
    if not sds_dir.exists():
        print(f"No {sds_dir} directory found.", file=sys.stderr)
        return 1
    index = load_index(index_path)
    known = {e.inv_num.upper() for e in index.entries}
    added = []
    for pdf in sorted(sds_dir.glob("*.pdf")):
        inv_num = pdf.stem.upper()
        if inv_num in known:
            continue
        rel = f"{config.sds_dir}/{pdf.name}"
        index.entries.append(SdsEntry(inv_num=inv_num, name=inv_num, mirror_path=rel))
        added.append(inv_num)
    if added:
        save_index(index, index_path)
    print(f"Added {len(added)} new entries: {', '.join(added) or '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
