# Guia para Download de Datasets Prioritários da ANATEL

Este guia é **versionado** (documentação). Os arquivos baixados/gerados devem ficar em pastas **ignoradas pelo git**.

## 🔗 Links Oficiais

- Portal ANATEL (dados abertos): https://dadosabertos.anatel.gov.br

## 🎯 Datasets Mais Importantes para Conectividade Rural

Sugestão de foco inicial (ajuste conforme o inventário atual):

- Backhaul / infraestrutura
- Estações / ERBs
- Banda larga fixa (acessos)

## 📁 Estrutura de Pastas Recomendada

> Caminho (portável): `data/manual/`

```
data/manual/
├── Inventario_de_Bases_de_Dados.csv   (inventário)
├── GUIA_DOWNLOAD_ANATEL.md            (este guia)
├── templates/                         (templates reutilizáveis)
├── raw_downloads/                     (IGNORADO pelo git)
├── processed/                         (IGNORADO pelo git)
└── outputs/                           (IGNORADO pelo git)
```

## 📋 Passo a passo (manual)

1. Acesse o portal de dados abertos.
2. Encontre o dataset desejado e escolha o período/recorte.
3. Prefira formatos estruturados (Parquet/CSV conforme disponibilidade).
4. Salve em `data/manual/raw_downloads/`.

## 🚀 Próximos Passos

1. Gere/atualize o guia automático (opcional):
   - `python -m data_pipeline.connectors.anatel_smart_connector --generate-guide`
2. Processe arquivos manuais quando necessário:
   - `python -m data_pipeline.connectors.anatel_smart_connector --process`
3. Rode o pipeline:
   - `python scripts/run_pipeline.py`

## ⚠️ Observações

- Não versionar dados brutos/outputs grandes: o `.gitignore` já cobre isso.
- Se algo aparecer no `git status`, rode: `python scripts/clean_manual_data.py`
