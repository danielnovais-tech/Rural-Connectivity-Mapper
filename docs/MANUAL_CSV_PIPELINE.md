# Manual CSV Data Pipeline

## Overview

Este pipeline foi projetado para processar dados ANATEL (ou outros) baixados manualmente em formato CSV. A estratégia é automatizar tudo **depois** do download manual - sem requisições HTTP à ANATEL.

## Funcionamento

### 1. Monitoramento de Pasta
O pipeline monitora a pasta `data/bronze/manual/` à espera de novos arquivos CSV.

### 2. Validação e Transformação
Quando um CSV é encontrado, o pipeline:
- ✅ Valida o formato e campos obrigatórios
- ✅ Transforma os dados para o schema unificado
- ✅ Aplica scores de confiança
- ✅ Enriquece com metadados

### 3. Versionamento
Para evitar duplicação:
- ✅ Calcula hash SHA256 de cada arquivo
- ✅ Registra arquivos processados em `.processed_files.json`
- ✅ Ignora arquivos já processados automaticamente

### 4. Integração
Os dados processados são integrados ao modelo unificado através das camadas:
- **Bronze**: Dados brutos e imutáveis
- **Silver**: Normalizados e validados com scores de confiança
- **Gold**: Agregados e prontos para análise

## Uso

### Formato CSV Esperado

O CSV deve conter no mínimo:
- `latitude` (obrigatório): Latitude em graus decimais
- `longitude` (obrigatório): Longitude em graus decimais  
- `timestamp` (obrigatório): Data/hora da medição

Campos opcionais (mas recomendados):
- `download` / `download_mbps`: Velocidade de download (Mbps)
- `upload` / `upload_mbps`: Velocidade de upload (Mbps)
- `latency` / `latency_ms`: Latência (ms)
- `provider`: Nome do provedor
- `technology`: Tipo de tecnologia (Fibra, 4G, Satélite, etc.)
- `city` / `municipality`: Cidade
- `state` / `uf`: Estado
- `id`: Identificador único (será gerado se omitido)

**Exemplo de CSV válido:**

```csv
id,latitude,longitude,timestamp,download,upload,latency,provider,technology,city,state
anatel_001,-23.5505,-46.6333,2026-01-15T10:00:00,100.5,20.3,30.2,Claro,Fibra Óptica,São Paulo,SP
anatel_002,-22.9068,-43.1729,2026-01-15T11:00:00,95.8,18.5,35.1,Vivo,Fibra Óptica,Rio de Janeiro,RJ
```

### Passo a Passo

#### 1. Coloque seus CSVs na pasta monitorada

```bash
# Copie seus arquivos CSV para:
cp seu_arquivo_anatel.csv data/bronze/manual/
```

#### 2. Execute o pipeline

Opção A - Pipeline completo (recomendado):
```bash
python scripts/demo_manual_csv.py
```

Opção B - Integrado com outras fontes:
```python
from src.pipeline import PipelineOrchestrator
from src.sources import ManualCSVSource, MockCrowdsourceSource

# Configure as fontes
sources = [
    ManualCSVSource(watch_dir="data/bronze/manual"),
    MockCrowdsourceSource(num_samples=50),
]

# Execute o pipeline
pipeline = PipelineOrchestrator()
pipeline.run(sources)
```

#### 3. Verifique os resultados

```bash
# Dados brutos (bronze)
ls -la data/bronze/anatel_manual/

# Dados processados (silver)
ls -la data/silver/

# Dados agregados (gold)
ls -la data/gold/
```

## Características Especiais

### ✅ Validação Rigorosa
- Campos obrigatórios verificados
- Valores numéricos validados (lat/lon, speeds)
- Linhas inválidas registradas e ignoradas
- Timestamps parseados em múltiplos formatos

### ✅ Flexibilidade
- Suporta delimitadores `,` e `;`
- Aceita variações de nomes de colunas (`latitude` ou `lat`, etc.)
- Tecnologias mapeadas automaticamente (Fibra, Satélite, 4G, etc.)
- Campos extras preservados em metadata

### ✅ Prevenção de Duplicatas
- Hash do arquivo calculado e registrado
- Reprocessamento automático evitado
- Log persistente em `.processed_files.json`

### ✅ Rastreabilidade
- Nome do arquivo fonte armazenado em metadata
- Número da linha preservado para debugging
- Todos os campos extras mantidos

## Comandos Úteis

### Ver arquivos processados
```bash
cat data/bronze/manual/.processed_files.json
```

### Reprocessar todos os arquivos
```bash
# CUIDADO: Isso irá reprocessar tudo!
rm data/bronze/manual/.processed_files.json
python scripts/demo_manual_csv.py
```

### Limpar dados processados
```bash
make clean
```

## Testes

Execute os testes do manual CSV source:

```bash
# Todos os testes
pytest tests/test_manual_csv_source.py -v

# Teste específico
pytest tests/test_manual_csv_source.py::TestManualCSVSource::test_fetch_basic_csv -v
```

## Exemplo Completo

Veja `examples/anatel_sample_manual.csv` para um exemplo completo de CSV válido.

## Integração com Outras Fontes

O ManualCSVSource pode ser facilmente combinado com outras fontes de dados:

```python
from src.sources import (
    ManualCSVSource,
    MockCrowdsourceSource,
    MockSpeedtestSource
)

sources = [
    ManualCSVSource(),  # Dados manuais ANATEL
    MockCrowdsourceSource(num_samples=50),  # Crowdsourcing
    MockSpeedtestSource(num_samples=30),  # Speedtests
]
```

## Troubleshooting

### Problema: "No CSV files found"
**Solução**: Verifique se há arquivos `.csv` em `data/bronze/manual/`

### Problema: "Row X: Invalid data"
**Solução**: Verifique se os campos obrigatórios (lat, lon, timestamp) estão presentes e válidos

### Problema: "Skipping already processed file"
**Solução**: O arquivo já foi processado. Para reprocessar, delete `.processed_files.json`

### Problema: Encoding errors
**Solução**: Certifique-se que o CSV está em UTF-8

## Arquitetura

```
Manual CSV Flow:
┌─────────────────────────────────────────┐
│ 1. Place CSV in data/bronze/manual/     │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 2. ManualCSVSource.fetch()              │
│    - Scan for new files                 │
│    - Check if already processed (hash)  │
│    - Parse CSV rows                     │
│    - Validate & transform               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 3. Bronze Layer                         │
│    - Store raw measurements             │
│    - Immutable storage                  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 4. Silver Layer                         │
│    - Normalize data                     │
│    - Calculate confidence scores        │
│    - Deduplicate                        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 5. Gold Layer                           │
│    - Aggregate by geography             │
│    - Analysis-ready datasets            │
└─────────────────────────────────────────┘
```

## Próximos Passos

1. ✅ Pipeline básico implementado
2. ✅ Validação e versionamento
3. ✅ Testes automatizados
4. 🔄 Adicionar mais validações específicas ANATEL
5. 🔄 Suporte para formatos adicionais (Excel, JSON)
6. 🔄 Interface web para upload de CSVs
