#!/usr/bin/env python3
"""Clean manual data artifacts under data/manual/.

Keeps versioned documentation/templates and deletes ignored artifacts like raw downloads
and processed outputs.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def _rm_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
        print(f"Removed dir: {path}")


def _rm_file(path: Path) -> None:
    if path.exists():
        path.unlink()
        print(f"Removed file: {path}")


def main() -> int:
    manual_dir = Path("data/manual")

    for subdir in ["raw_downloads", "processed", "outputs", "processados"]:
        _rm_tree(manual_dir / subdir)

    for ext in [".csv", ".parquet", ".json", ".xlsx", ".pdf"]:
        for file_path in manual_dir.glob(f"*{ext}"):
            _rm_file(file_path)

    print("Done. Preserved:")
    print("- data/manual/GUIA_DOWNLOAD_ANATEL.md")
    print("- data/manual/templates/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
