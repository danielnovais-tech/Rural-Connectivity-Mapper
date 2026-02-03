from __future__ import annotations  # noqa: I001
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "BLUEPRINT.md"


@dataclass(frozen=True)
class RepoFile:
    path: Path
    title_en: str
    title_pt: str


KEY_ENTRYPOINTS: list[RepoFile] = [
    RepoFile(REPO_ROOT / "scripts" / "run_pipeline.py", "Pipeline runner", "Executor do pipeline"),
    RepoFile(REPO_ROOT / "main.py", "CLI entrypoint", "Entrypoint do CLI"),
    RepoFile(REPO_ROOT / "app.py", "Web app (Flask)", "App web (Flask)"),
    RepoFile(REPO_ROOT / "dashboard.py", "Dashboard (Streamlit)", "Dashboard (Streamlit)"),
    RepoFile(REPO_ROOT / "crowdsource_server.py", "Crowdsourcing server", "Servidor de crowdsourcing"),
]

KEY_DOCS: list[RepoFile] = [
    RepoFile(REPO_ROOT / "docs" / "DEV_SETUP.md", "Developer setup", "Setup de desenvolvimento"),
    RepoFile(REPO_ROOT / "docs" / "ARCHITECTURE_DATA.md", "Data architecture", "Arquitetura de dados"),
    RepoFile(REPO_ROOT / "docs" / "FUSION_ENGINE.md", "Fusion engine", "Fusion engine"),
    RepoFile(REPO_ROOT / "docs" / "API.md", "API", "API"),
    RepoFile(REPO_ROOT / "docs" / "CROWDSOURCING.md", "Crowdsourcing", "Crowdsourcing"),
    RepoFile(REPO_ROOT / "docs" / "WEB_DASHBOARD.md", "Web dashboard", "Dashboard web"),
]


EXCLUDE_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    "node_modules",
    "data",
    "bronze",
    "stress_artifacts",
}


def _strip_jsonc(text: str) -> str:
    """Strip // and /* */ comments from JSONC while preserving string literals."""

    out: list[str] = []
    i = 0
    in_string = False
    escape = False
    while i < len(text):
        ch = text[i]

        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue

        if ch == "/" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt == "/":
                i += 2
                while i < len(text) and text[i] not in "\r\n":
                    i += 1
                continue
            if nxt == "*":
                i += 2
                while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue

        out.append(ch)
        i += 1

    return "".join(out)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            return json.loads(_strip_jsonc(raw))
        except json.JSONDecodeError:
            return None


def _rel(p: Path) -> str:
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except Exception:
        return p.as_posix()


def _link(path: Path) -> str:
    return f"[{_rel(path)}]({_rel(path)})"


def _heading(en: str, pt: str, level: int = 2) -> str:
    prefix = "#" * max(1, min(level, 6))
    return f"{prefix} {en} / {pt}"


def _list_existing(files: list[RepoFile]) -> list[RepoFile]:
    return [f for f in files if f.path.exists()]


def _scan_tree(root: Path, *, max_depth: int, include_files: bool = False) -> list[str]:
    """Return a deterministic, readable tree for selected roots."""

    lines: list[str] = []
    root = Path(root)

    def walk(base: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return

        children = []
        try:
            children = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception:
            return

        filtered: list[Path] = []
        for child in children:
            if child.name in EXCLUDE_DIR_NAMES:
                continue
            if child.is_dir():
                filtered.append(child)
            elif include_files:
                if child.suffix.lower() in {".py", ".md", ".json", ".toml", ".yml", ".yaml"}:
                    filtered.append(child)

        for idx, child in enumerate(filtered):
            is_last = idx == len(filtered) - 1
            branch = "└── " if is_last else "├── "
            lines.append(f"{prefix}{branch}{child.name}{'/' if child.is_dir() else ''}")
            if child.is_dir():
                walk(child, prefix + ("    " if is_last else "│   "), depth + 1)

    lines.append(f"{root.name}/")
    walk(root, "", 1)
    return lines


def _extract_flask_routes(py_path: Path) -> list[str]:
    if not py_path.exists() or py_path.suffix != ".py":
        return []

    text = py_path.read_text(encoding="utf-8", errors="replace")
    routes: set[str] = set()

    for match in re.finditer(r"@(?:\w+\.)?route\(\s*([\"'])(.+?)\1", text):
        routes.add(match.group(2))

    for match in re.finditer(r"@(?:\w+\.)?app\.route\(\s*([\"'])(.+?)\1", text):
        routes.add(match.group(2))

    return sorted(routes)


def _render() -> str:
    now = datetime.now(UTC).isoformat()
    tasks_json = _read_json(REPO_ROOT / ".vscode" / "tasks.json")
    launch_json = _read_json(REPO_ROOT / ".vscode" / "launch.json")

    sections: list[str] = []

    sections.append("# Architecture Blueprint / Blueprint de Arquitetura\n")
    sections.append(
        "AUTO-GENERATED FILE — do not edit manually.\\n"
        "Arquivo AUTO-GERADO — não edite manualmente.\\n\\n"
        f"Generated at / Gerado em: {now}\\n"
        "Regenerate / Regenerar: `python scripts/generate_blueprint.py`\n"
    )

    sections.append("\n" + _heading("Executive Summary", "Resumo Executivo", 2) + "\n")
    sections.append(
        "This repository implements a rural connectivity mapping platform: ingestion from multiple sources, "
        "a medallion-style pipeline (Bronze→Silver→Gold), analytics/fusion scoring, and web/dashboard surfaces.\\n"
        "Este repositório implementa uma plataforma de mapeamento de conectividade rural: ingestão de múltiplas fontes, "
        "um pipeline estilo medallion (Bronze→Silver→Gold), score/fusão analítica e interfaces web/dashboard.\n"
    )

    sections.append("\n" + _heading("Entrypoints", "Entrypoints", 2) + "\n")
    existing_entrypoints = _list_existing(KEY_ENTRYPOINTS)
    if existing_entrypoints:
        for f in existing_entrypoints:
            sections.append(f"- {_link(f.path)} — {f.title_en} / {f.title_pt}\n")
    else:
        sections.append("- (none detected) / (nenhum detectado)\n")

    sections.append("\n" + _heading("Core Architecture", "Arquitetura Central", 2) + "\n")
    sections.append(
        "- Canonical schema / Esquema canônico: "
        f"{_link(REPO_ROOT / 'src' / 'schemas' / 'measurement.py')}\n"
        "- Pipeline orchestrator / Orquestrador: "
        f"{_link(REPO_ROOT / 'src' / 'pipeline' / 'orchestrator.py')}\n"
        "- Pipeline layers / Camadas: "
        f"{_link(REPO_ROOT / 'src' / 'pipeline' / 'bronze.py')}, "
        f"{_link(REPO_ROOT / 'src' / 'pipeline' / 'silver.py')}, "
        f"{_link(REPO_ROOT / 'src' / 'pipeline' / 'gold.py')}\n"
        "- Fusion engine / Motor de fusão: "
        f"{_link(REPO_ROOT / 'src' / 'pipeline' / 'fusion_engine.py')}\n"
        "- Sources / Fontes: "
        f"{_link(REPO_ROOT / 'src' / 'sources' / '__init__.py')}\n"
        "- Connectors (ANATEL, etc.) / Conectores: "
        f"{_link(REPO_ROOT / 'data_pipeline' / 'connectors' / '__init__.py')}\n"
    )

    sections.append("\n" + _heading("Repo Map (high-level)", "Mapa do Repositório (alto nível)", 2) + "\n")
    roots = [REPO_ROOT / "src", REPO_ROOT / "scripts", REPO_ROOT / "docs", REPO_ROOT / "data_pipeline"]
    for r in roots:
        if not r.exists():
            continue
        tree_lines = _scan_tree(r, max_depth=2, include_files=False)
        sections.append(f"\n**{_rel(r)}**\n\n")
        sections.append("```\n" + "\n".join(tree_lines) + "\n```\n")

    sections.append("\n" + _heading("VS Code Workflows", "Workflows do VS Code", 2) + "\n")
    if tasks_json and isinstance(tasks_json.get("tasks"), list):
        task_labels = [t.get("label") for t in tasks_json["tasks"] if isinstance(t, dict)]
        task_labels = [x for x in task_labels if isinstance(x, str) and x.strip()]
        sections.append("**Tasks / Tarefas**\n\n")
        for label in sorted(set(task_labels), key=str.lower):
            sections.append(f"- {label}\n")
        sections.append("\n")
    else:
        sections.append(f"- Could not parse tasks.json / Não foi possível ler tasks.json: {_link(REPO_ROOT / '.vscode' / 'tasks.json')}\n")

    if launch_json and isinstance(launch_json.get("configurations"), list):
        names = [c.get("name") for c in launch_json["configurations"] if isinstance(c, dict)]
        names = [x for x in names if isinstance(x, str) and x.strip()]
        sections.append("**Launch configs / Configurações de debug**\n\n")
        for name in sorted(set(names), key=str.lower):
            sections.append(f"- {name}\n")
        sections.append("\n")

    sections.append("\n" + _heading("APIs (best-effort)", "APIs (best-effort)", 2) + "\n")
    for py in [REPO_ROOT / "app.py", REPO_ROOT / "crowdsource_server.py"]:
        routes = _extract_flask_routes(py)
        if not routes:
            continue
        sections.append(f"**{_rel(py)}**\n\n")
        for r in routes:
            sections.append(f"- `{r}`\n")
        sections.append("\n")

    sections.append("\n" + _heading("Key Docs", "Docs Importantes", 2) + "\n")
    existing_docs = _list_existing(KEY_DOCS)
    if existing_docs:
        for d in existing_docs:
            sections.append(f"- {_link(d.path)} — {d.title_en} / {d.title_pt}\n")
    else:
        sections.append("- (none detected) / (nenhum detectado)\n")

    sections.append("\n" + _heading("Notes", "Notas", 2) + "\n")
    sections.append(
        "- This blueprint is intentionally high-level; deeper details live in docs/.\\n"
        "- Este blueprint é propositalmente alto nível; detalhes estão em docs/.\n"
    )

    return "".join(sections).rstrip() + "\n"


def main() -> None:
    output_path = DEFAULT_OUTPUT
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render(), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
