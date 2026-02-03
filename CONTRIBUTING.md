# Contributing to Rural Connectivity Mapper 2026 - ANATEL Integration

Obrigado por contribuir! Este guia é **Windows-first** e orientado a **VS Code Tasks**.

## 🚀 Quick Start (5 minutos)

### Pré-requisitos

- Python **3.12+** (mínimo). Observação: o CI valida Python 3.12–3.13.
- Git
- VS Code (recomendado) + extensões sugeridas em [.vscode/extensions.json](.vscode/extensions.json)

### Setup rápido (VS Code)

1. Abra o repositório no VS Code.
2. Execute `Tasks: Run Task` e rode, na ordem:
   - **Bootstrap: Create .venv (system python)**
   - **Setup: Install deps + quick checks**
3. Valide o ambiente:
   - **Pytest (repo)**

### ANATEL (opcional)

- Gerar guia de download: **ANATEL: Generate download guide**
- Rodar pipeline com Parquet ANATEL: **Pipeline: Run (include ANATEL parquet)**

Mais detalhes: [docs/DEV_SETUP.md](docs/DEV_SETUP.md).

## 🔧 Ambiente de Desenvolvimento

### Convenções do repositório

- Interpretador padrão no VS Code: `.venv/Scripts/python.exe` (Windows)
- Lint/format: Ruff (config em [ruff.toml](ruff.toml))
- Tipos: mypy (executado via tasks/scripts)
- Testes: pytest

### Tasks principais (labels exatos)

- Setup:
  - **Setup: Install deps + quick checks** (usa [scripts/setup_environment.py](scripts/setup_environment.py))
- Qualidade:
  - **Lint+Types: Ruff + mypy** (usa [scripts/run_linting.py](scripts/run_linting.py))
  - **Ruff (format)** / **Ruff (check)** (opcionais)
- Testes:
  - **Pytest (repo)** / **Pytest (repo, no capture)**
- Pipeline:
  - **Pipeline: Run (default)**
  - **Pipeline: Run (include ANATEL parquet)**

## 📁 Estrutura do Projeto

### Visão geral (Medallion)

- **Bronze**: ingestão “raw/imutável” por fonte
- **Fusion/Silver**: normalização/validação/dedupe + enriquecimento
- **Gold**: agregações e datasets prontos para análise/consumo

Principais pastas:

- `src/` — pipeline, schemas, qualidade, utils
- `data_pipeline/` — conectores e orquestração de ingestão
- `scripts/` — entrypoints (pipeline, exportadores, setup)
- `tests/` — suíte de testes

### Integração ANATEL (paths reais)

- Downloads/manuais: `data/manual/` (guia versionado; dados brutos ignorados pelo git)
- Saídas bronze do conector: `data/bronze/anatel/`
- Export agregador (exemplo): `data/bronze/anatel_acesso_fixo/`

## 🔄 Fluxo de Trabalho

1. Fork → branch → implementar
2. Rodar tasks do VS Code (qualidade, testes, pipeline)
3. Abrir Pull Request usando o template

### Branch naming

- `feat/anatel-*` — novas funcionalidades ANATEL
- `fix/anatel-*` — correções na integração
- `docs/anatel-*` — documentação
- `test/anatel-*` — testes específicos

### Commits (conventional commits)

Exemplos:

- `feat(anatel): add strict mode validation`
- `fix(anatel): correct column mapping for tecnologia`
- `docs(anatel): update download guide`
- `test(anatel): add strict mode test cases`

### Pull Request

- Use o template: [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)
- Checklist mínimo antes do PR:
  - **Lint+Types: Ruff + mypy**
  - **Pytest (repo)**
  - Se mexeu em pipeline/dados: rode **Pipeline: Run (default)**

## 🧪 Testes & Qualidade

### Ruff (lint/format)

- Preferência local: use a task **Lint+Types: Ruff + mypy**
- Alternativo (terminal):
  - `python -m ruff format src tests`
  - `python -m ruff check src tests --fix`

### mypy (tipos)

- Preferência local: use a task **Lint+Types: Ruff + mypy**
- Alternativo (terminal): `python -m mypy src --ignore-missing-imports`

### pytest

- Task principal: **Pytest (repo)**
- Dica: o `pytest.ini` tem markers (ex.: `integration`, `slow`) e configurações padrão.

### Nota sobre Flake8 (legado)

O CI ainda roda Flake8 (legado). Localmente, o fluxo recomendado é Ruff + mypy, mas evite introduzir padrões que quebrem checagens legadas.

## 📊 Dados ANATEL

### Guia rápido

- Leia/atualize o guia versionado: [data/manual/GUIA_DOWNLOAD_ANATEL.md](data/manual/GUIA_DOWNLOAD_ANATEL.md)
- Para export agregado (acesso_fixo):
  - Task: **ANATEL: Export acesso_fixo**

### Pastas e higiene

- `data/manual/raw_downloads/`, `processed/`, `outputs/` são ignoradas pelo git.
- Se algo aparecer no `git status`, rode: **Clean: manual data artifacts**.
