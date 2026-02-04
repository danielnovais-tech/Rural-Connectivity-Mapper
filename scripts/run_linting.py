#!/usr/bin/env python3
"""Run Ruff + mypy checks.

Designed to be Windows-friendly and to run using the currently active interpreter.

TEMP_APPLYPATCH_MARKER
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def run_step(args: list[str], title: str) -> bool:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    completed = subprocess.run(args, check=False)
    if completed.returncode != 0:
        print(f"FAILED ({completed.returncode})")
        return False
    print("OK")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Ruff + mypy (optionally best-effort).")
    parser.add_argument(
        "--best-effort",
        action="store_true",
        help="Do not fail the process if checks fail (exit 0).",
    )
    parser.add_argument(
        "--format",
        action="store_true",
        help="Run ruff format on src/tests before checking.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run ruff check with --fix on src/tests.",
    )
    args = parser.parse_args()

    ok = True

    if args.format:
        ok &= run_step([sys.executable, "-m", "ruff", "format", "src", "tests"], "Ruff: format")

    ruff_check_cmd = [sys.executable, "-m", "ruff", "check", "src", "tests"]
    if args.fix:
        ruff_check_cmd.append("--fix")
    ok &= run_step(ruff_check_cmd, "Ruff: check")

    ok &= run_step(
        [sys.executable, "-m", "mypy", "src", "--ignore-missing-imports"],
        "mypy: type check",
    )

    if args.best_effort:
        return 0

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
