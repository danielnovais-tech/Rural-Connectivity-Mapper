from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path


def _default_appdata_dir() -> Path:
    # Prefer LOCALAPPDATA on Windows, fall back to home.
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        return Path(base) / "RuralMapper"
    return Path.home() / ".rural_mapper"


def _ensure_runtime_data_dir() -> Path:
    data_dir = Path(os.environ.get("RURAL_MAPPER_DATA_DIR") or _default_appdata_dir())
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["RURAL_MAPPER_DATA_DIR"] = str(data_dir)
    return data_dir


def _run_script(path: Path, argv: list[str]) -> int:
    old_argv = sys.argv
    try:
        sys.argv = [str(path)] + argv
        runpy.run_path(str(path), run_name="__main__")
        return 0
    finally:
        sys.argv = old_argv


def _run_streamlit_dashboard(dashboard_py: Path, argv: list[str]) -> int:
    # Streamlit is click-based; invoke its CLI entry within this process so it works in a frozen EXE.
    try:
        from streamlit.web import cli as st_cli  # type: ignore
    except Exception as exc:
        print(f"Streamlit is not available: {exc}")
        return 2

    old_argv = sys.argv
    try:
        sys.argv = ["streamlit", "run", str(dashboard_py)] + argv
        st_cli.main()
        return 0
    finally:
        sys.argv = old_argv


def main(argv: list[str] | None = None) -> int:
    # Important when frozen on Windows (joblib/sklearn/spawn).
    try:
        import multiprocessing

        multiprocessing.freeze_support()
    except Exception:
        pass

    _ensure_runtime_data_dir()

    parser = argparse.ArgumentParser(prog="rural-mapper", description="Rural Connectivity Mapper (Windows EXE launcher)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cli = sub.add_parser("cli", help="Run main CLI (main.py)")
    p_cli.add_argument("args", nargs=argparse.REMAINDER)

    p_pipeline = sub.add_parser("pipeline", help="Run pipeline runner (scripts/run_pipeline.py)")
    p_pipeline.add_argument("args", nargs=argparse.REMAINDER)

    p_web = sub.add_parser("web", help="Run Flask web app (app.py)")
    p_web.add_argument("args", nargs=argparse.REMAINDER)

    p_crowd = sub.add_parser("crowdsource", help="Run crowdsourcing server (crowdsource_server.py)")
    p_crowd.add_argument("args", nargs=argparse.REMAINDER)

    p_dash = sub.add_parser("dashboard", help="Run Streamlit dashboard (dashboard.py)")
    p_dash.add_argument("args", nargs=argparse.REMAINDER)

    p_blue = sub.add_parser("blueprint", help="Generate docs/BLUEPRINT.md")
    p_blue.add_argument("args", nargs=argparse.REMAINDER)

    args_ns = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent

    if args_ns.cmd == "cli":
        return _run_script(repo_root / "main.py", list(args_ns.args))

    if args_ns.cmd == "pipeline":
        return _run_script(repo_root / "scripts" / "run_pipeline.py", list(args_ns.args))

    if args_ns.cmd == "web":
        return _run_script(repo_root / "app.py", list(args_ns.args))

    if args_ns.cmd == "crowdsource":
        return _run_script(repo_root / "crowdsource_server.py", list(args_ns.args))

    if args_ns.cmd == "dashboard":
        return _run_streamlit_dashboard(repo_root / "dashboard.py", list(args_ns.args))

    if args_ns.cmd == "blueprint":
        return _run_script(repo_root / "scripts" / "generate_blueprint.py", list(args_ns.args))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
