# Architecture Blueprint / Blueprint de Arquitetura
AUTO-GENERATED FILE — do not edit manually.\nArquivo AUTO-GERADO — não edite manualmente.\n\nGenerated at / Gerado em: 2026-02-03T18:08:53.555714+00:00\nRegenerate / Regenerar: `python scripts/generate_blueprint.py`

## Executive Summary / Resumo Executivo
This repository implements a rural connectivity mapping platform: ingestion from multiple sources, a medallion-style pipeline (Bronze→Silver→Gold), analytics/fusion scoring, and web/dashboard surfaces.\nEste repositório implementa uma plataforma de mapeamento de conectividade rural: ingestão de múltiplas fontes, um pipeline estilo medallion (Bronze→Silver→Gold), score/fusão analítica e interfaces web/dashboard.

## Entrypoints / Entrypoints
- [scripts/run_pipeline.py](scripts/run_pipeline.py) — Pipeline runner / Executor do pipeline
- [main.py](main.py) — CLI entrypoint / Entrypoint do CLI
- [app.py](app.py) — Web app (Flask) / App web (Flask)
- [dashboard.py](dashboard.py) — Dashboard (Streamlit) / Dashboard (Streamlit)
- [crowdsource_server.py](crowdsource_server.py) — Crowdsourcing server / Servidor de crowdsourcing

## Core Architecture / Arquitetura Central
- Canonical schema / Esquema canônico: [src/schemas/measurement.py](src/schemas/measurement.py)
- Pipeline orchestrator / Orquestrador: [src/pipeline/orchestrator.py](src/pipeline/orchestrator.py)
- Pipeline layers / Camadas: [src/pipeline/bronze.py](src/pipeline/bronze.py), [src/pipeline/silver.py](src/pipeline/silver.py), [src/pipeline/gold.py](src/pipeline/gold.py)
- Fusion engine / Motor de fusão: [src/pipeline/fusion_engine.py](src/pipeline/fusion_engine.py)
- Sources / Fontes: [src/sources/__init__.py](src/sources/__init__.py)
- Connectors (ANATEL, etc.) / Conectores: [data_pipeline/connectors/__init__.py](data_pipeline/connectors/__init__.py)

## Repo Map (high-level) / Mapa do Repositório (alto nível)

**src**

```
src/
├── models/
├── pipeline/
├── quality/
├── schemas/
├── sources/
└── utils/
```

**scripts**

```
scripts/
└── stress/
```

**docs**

```
docs/
```

**data_pipeline**

```
data_pipeline/
├── anatel/
└── connectors/
```

## VS Code Workflows / Workflows do VS Code
**Tasks / Tarefas**

- ANATEL: Export acesso_fixo
- ANATEL: Generate download guide
- ANATEL: Process manual CSVs
- ANATEL: Show priority
- Bootstrap: Create .venv (system python)
- Build: Windows EXE (PyInstaller)
- Clean: manual data artifacts
- Coverage (open html)
- Docs: Generate blueprint
- Lint+Types (strict): Ruff + mypy
- Lint+Types: Ruff + mypy
- Pipeline: Run (default)
- Pipeline: Run (include ANATEL parquet)
- Pytest (coverage)
- Pytest (repo)
- Pytest (repo, no capture)
- Ruff (check)
- Ruff (format)
- Setup: Install deps + quick checks

**Launch configs / Configurações de debug**

- ANATEL: acesso_fixo export
- Pipeline: run_pipeline.py (default)
- Pipeline: run_pipeline.py (include ANATEL parquet)
- Server: crowdsource_server.py
- Web: app.py
- Web: dashboard.py


## APIs (best-effort) / APIs (best-effort)
**app.py**

- `/`
- `/api/analysis`
- `/api/data`
- `/api/data/<point_id>`
- `/api/health`
- `/api/map`
- `/api/report/<report_format>`
- `/api/simulate`
- `/api/statistics`
- `/api/v2/recommendation`

**crowdsource_server.py**

- `/`
- `/api/submit`
- `/api/template`
- `/api/upload-csv`
- `/health`


## Key Docs / Docs Importantes
- [docs/DEV_SETUP.md](docs/DEV_SETUP.md) — Developer setup / Setup de desenvolvimento
- [docs/ARCHITECTURE_DATA.md](docs/ARCHITECTURE_DATA.md) — Data architecture / Arquitetura de dados
- [docs/FUSION_ENGINE.md](docs/FUSION_ENGINE.md) — Fusion engine / Fusion engine
- [docs/API.md](docs/API.md) — API / API
- [docs/CROWDSOURCING.md](docs/CROWDSOURCING.md) — Crowdsourcing / Crowdsourcing
- [docs/WEB_DASHBOARD.md](docs/WEB_DASHBOARD.md) — Web dashboard / Dashboard web

## Notes / Notas
- This blueprint is intentionally high-level; deeper details live in docs/.\n- Este blueprint é propositalmente alto nível; detalhes estão em docs/.
