# Rural Connectivity Mapper 2026

A comprehensive platform for mapping, analyzing, and improving rural connectivity across Latin America and beyond.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (recommended: 3.12)
- pip package manager

### Data Pipeline (Pilar 1: Source of Truth)

The data pipeline processes connectivity measurements through a robust bronze/silver/gold architecture with quality scoring.

**Run the complete pipeline:**

```bash
# Install dependencies
make install

# Run end-to-end pipeline
make data-build

# Run tests
make test
```

**What happens:**
1. **Bronze Layer**: Ingests raw data from multiple sources (immutable storage)
2. **Silver Layer**: Normalizes, validates, deduplicates, and adds confidence scores
3. **Gold Layer**: Aggregates data for geographic and analytical consumption

**Output:** Enriched data with confidence scores in `data/gold/full_dataset_*.json`

### Understanding Confidence Scores

Every measurement includes a **confidence score (0-100)** calculated from:

- **Recency (40%)**: How fresh is the data?
- **Source Reliability (30%)**: How trustworthy is the source? (ANATEL: 95%, Crowdsource: 60%, etc.)
- **Consistency (20%)**: Are values within expected ranges?
- **Completeness (10%)**: How complete is the metadata?

Higher scores = more reliable data for decision-making.

**Example:**
```json
{
  "id": "measurement_123",
  "lat": -15.7801,
  "lon": -47.9292,
  "download_mbps": 100.5,
  "upload_mbps": 20.3,
  "source": "anatel",
  "confidence_score": 87.5,
  "confidence_breakdown": {
    "recency_score": 100.0,
    "source_reliability_score": 95.0,
    "consistency_score": 85.0,
    "completeness_score": 70.0
  }
}
```

## 📚 Documentation

- **[Data Architecture Guide](docs/ARCHITECTURE_DATA.md)** - Complete pipeline documentation, schema definitions, and confidence scoring methodology
- **[API Documentation](docs/API.md)** - API reference
- **[Multi-Country Support](docs/MULTI_COUNTRY.md)** - International deployment
- **[Crowdsourcing Guide](docs/CROWDSOURCING.md)** - Community data collection
- **[Developer Setup (Windows-first)](docs/DEV_SETUP.md)** - VS Code tasks, environment setup, and daily workflow
- **[Simulation Pipeline Spec](docs/SIMULATION_PIPELINE.md)** - Research-grade direction + CLI scaffold
- **[GR801 SoC Simulation (Standalone)](docs/GR801_SIMULATION.md)** - Run the GR801 demo without touching the main pipeline

## 🏗️ Architecture Overview

### Data Pipeline (Bronze → Silver → Gold)

```
Sources (Crowdsource, ANATEL, etc.)
    ↓
Bronze Layer (Raw, Immutable)
    ↓
Silver Layer (Normalized, Validated, Confidence Scored)
    ↓
Gold Layer (Aggregated, Analysis-Ready)
```

### Key Features

- **Quality First**: Confidence scoring on all measurements
- **Reproducible**: Immutable bronze layer, versioned transformations
- **Extensible**: Easy to add new data sources
- **Geographic Aggregation**: H3 hexagonal spatial indexing
- **Data Contracts**: Pydantic schemas ensure data quality

## 🛠️ Development

This project supports Python 3.10+ (CI runs 3.10–3.12).

### Available Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make data-build     # Run data pipeline
make test           # Run all tests
make test-quality   # Run quality/confidence tests only
make clean          # Clean generated data files
```

### VS Code Tasks (Windows-friendly)

If you’re developing on Windows (or prefer one-click workflows), use the VS Code tasks in [.vscode/tasks.json](.vscode/tasks.json).

- Setup: **Setup: Install deps + quick checks**
- Lint/Types: **Lint+Types: Ruff + mypy**
- Tests: **Pytest (repo)**
- Pipeline: **Pipeline: Run (default)** / **Pipeline: Run (include ANATEL parquet)**

See [docs/DEV_SETUP.md](docs/DEV_SETUP.md) for the full workflow.

### Project Structure

```
src/
├── schemas/        # Canonical data schemas (Pydantic)
├── sources/        # Data source connectors
├── pipeline/       # Bronze/Silver/Gold pipeline
├── quality/        # Confidence scoring
├── models/         # Legacy models (ConnectivityPoint, etc.)
└── utils/          # Utility functions

data/
├── bronze/         # Raw immutable data by source
├── silver/         # Normalized & enriched data
└── gold/           # Aggregated analysis-ready data

tests/
├── test_schemas.py             # Schema validation tests
├── test_quality_confidence.py  # Confidence scoring tests
└── ...
```

## 📊 Data Sources

Currently supported sources:

- **Manual CSV** (production-ready): Process manually downloaded CSV files from ANATEL or other sources with automated validation and versioning. See [Manual CSV Pipeline Guide](docs/MANUAL_CSV_PIPELINE.md)
- **Mock Crowdsource** (demo): Simulates community-submitted measurements
- **Mock Speedtest** (demo): Simulates professional speed tests
- **Extensible**: Add real sources by implementing the `DataSource` interface

Future sources: ANATEL API, IBGE, Starlink Coverage API, Public Speedtest Platforms

### 🆕 Manual CSV Pipeline (New!)

For processing manually downloaded ANATEL data or other CSV files:

```bash
# 1. Place your CSV files in the monitored folder
cp your_anatel_data.csv data/bronze/manual/

# 2. Run the pipeline
python scripts/demo_manual_csv.py

# Or integrate with other sources
make data-build
```

**Features:**
- ✅ Automatic file monitoring and processing
- ✅ Duplicate prevention via file hashing
- ✅ Flexible CSV format support
- ✅ Full validation and transformation
- ✅ Integrated confidence scoring

#### CSV templates

**Basic template (recommended starting point):**

```csv
id,city,provider,latitude,longitude,download,upload,latency,jitter,packet_loss,timestamp
1,Your City Name,Your ISP Name,-23.5505,-46.6333,100.0,15.0,30.0,5.0,0.5,2026-01-15T10:00:00
```

**Complete template (example dataset):**

```csv
id,city,provider,latitude,longitude,download,upload,latency,jitter,packet_loss,timestamp
1,São Paulo,Starlink,-23.5505,-46.6333,165.4,22.8,28.5,3.2,0.1,2026-01-15T10:30:00
2,Belo Horizonte,Claro,-19.9167,-43.9345,92.1,15.3,38.7,6.5,0.8,2026-01-15T11:00:00
3,Curitiba,Vivo,-25.4284,-49.2733,110.5,18.2,32.1,4.8,0.3,2026-01-15T11:30:00
4,Porto Alegre,TIM,-30.0346,-51.2177,88.7,14.1,42.3,7.2,1.1,2026-01-15T12:00:00
5,Manaus,Viasat,-3.1190,-60.0217,75.3,9.8,68.2,15.7,2.5,2026-01-15T12:30:00
```

See the [complete guide](docs/MANUAL_CSV_PIPELINE.md) for details.

## Roadmap (alto nível)

| Área                          | Hoje                                                                 | Futuro                                                          | Próximo passo                                                                 |
|-------------------------------|----------------------------------------------------------------------|------------------------------------------------------------------|------------------------------------------------------------------------------|
| Qualidade dos Dados           | Dados de demonstração/ANATEL/IBGE; coleta manual/crowdsourcing.     | Fonte da Verdade global, em tempo real, auditável e padrão-ouro.  | Criar um pipeline robusto de ingestão, validação e fusão de dados heterogêneos (satélite, crowdsourcing, provedores). |
| Experiência do Usuário (UX)   | Painel Streamlit e CLI funcionais, mas voltados para técnicos.      | Interface inclusiva e acionável para todos (agricultor, governante, engenheiro). | Redesenhar o fluxo de usuário focando em "o que posso fazer?" e otimizar para conexões lentas. |
| Inteligência & Automação      | Análise básica e simulação de roteador.                              | Sistema de recomendação prescritivo e previsão de gaps de cobertura. | Implementar modelos de ML para prever necessidades e otimizar investimentos em infraestrutura. |
| Interoperabilidade & Ecossistema | Foco na América Latina e Starlink.                                   | Plataforma aberta e hub central para o ecossistema de conectividade global. | Publicar APIs padronizadas (OpenAPI) e formatos de dados abertos para integração nativa. |
| Sustentabilidade & Governança   | Projeto individual/open source.                                       | Modelo sustentável com governança clara e comunidade ativa. | Estabelecer um modelo de governança (ex: Open Source Foundation) e roadmap público.