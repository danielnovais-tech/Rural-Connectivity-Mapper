import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str], *, check: bool) -> int:
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.returncode


def setup_environment(*, strict: bool) -> None:
    print("🚀 Configurando ambiente de desenvolvimento...")

    req = REPO_ROOT / "requirements.txt"
    req_dev = REPO_ROOT / "requirements-dev.txt"

    if req.exists():
        _run([sys.executable, "-m", "pip", "install", "-r", str(req)], check=True)
    if req_dev.exists():
        _run([sys.executable, "-m", "pip", "install", "-r", str(req_dev)], check=True)

    precommit_cfg = REPO_ROOT / ".pre-commit-config.yaml"
    if not precommit_cfg.exists():
        precommit_cfg.write_text(
            """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
""",
            encoding="utf-8",
        )
        print("✅ Criado .pre-commit-config.yaml (Ruff)")
    else:
        print("ℹ️  .pre-commit-config.yaml já existe; não foi alterado")

    if strict:
        _run([sys.executable, "-m", "pre_commit", "install"], check=False)


def run_linting(*, strict: bool) -> None:
    print("🔍 Executando linting...")

    # Repo-wide ruff ainda falha por débito técnico; por padrão rodamos só em src/tests.
    _run([sys.executable, "-m", "ruff", "format", "src", "tests"], check=strict)
    _run([sys.executable, "-m", "ruff", "check", "--fix", "src", "tests"], check=strict)


def run_typing(*, strict: bool) -> None:
    print("🧠 Executando verificação de tipos...")
    _run(
        [sys.executable, "-m", "mypy", "src", "--ignore-missing-imports"],
        check=strict,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup + linting (best effort por padrão).")
    parser.add_argument("--strict", action="store_true", help="Falha se lint/typecheck falhar")
    parser.add_argument("--skip-install", action="store_true", help="Não instala dependências")
    parser.add_argument("--skip-lint", action="store_true", help="Não executa ruff")
    parser.add_argument("--skip-typing", action="store_true", help="Não executa mypy")
    args = parser.parse_args()

    if not args.skip_install:
        setup_environment(strict=args.strict)

    if not args.skip_lint:
        run_linting(strict=args.strict)

    if not args.skip_typing:
        run_typing(strict=args.strict)


if __name__ == "__main__":
    main()
