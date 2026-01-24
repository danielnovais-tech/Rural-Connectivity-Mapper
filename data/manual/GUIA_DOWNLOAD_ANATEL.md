# Guia para Download de Datasets Prioritários da ANATEL

**Gerado automaticamente em:** 2026-01-24 18:19:00

## 🎯 Datasets Mais Importantes para Conectividade Rural

### 1. Cobertura Móvel
- **Descrição:** Dados de cobertura da telefonia móvel
- **Prioridade:** ALTA (Infraestrutura física)
- **Atualização:** Mensal
- **Link direto:** [https://dados.gov.br/dataset/cobertura](https://dados.gov.br/dataset/cobertura)
- **Instruções:** Acesse o link acima, procure pela opção de download (geralmente CSV ou ZIP)
- **Salve como:** `Cobertura_Móvel_{DATA}.csv`
- **Coloque em:** `/home/runner/work/Rural-Connectivity-Mapper-2026/Rural-Connectivity-Mapper-2026/data/manual/`

### 2. Estações Rádio
- **Descrição:** Estações de rádio com coordenadas
- **Prioridade:** ALTA (Infraestrutura física)
- **Atualização:** Mensal
- **Link direto:** [https://dados.gov.br/dataset/estacoes](https://dados.gov.br/dataset/estacoes)
- **Instruções:** Acesse o link acima, procure pela opção de download (geralmente CSV ou ZIP)
- **Salve como:** `Estações_Rádio_{DATA}.csv`
- **Coloque em:** `/home/runner/work/Rural-Connectivity-Mapper-2026/Rural-Connectivity-Mapper-2026/data/manual/`

## 📁 Estrutura de Pastas Recomendada
```
/home/runner/work/Rural-Connectivity-Mapper-2026/Rural-Connectivity-Mapper-2026/data/manual/
├── Inventario_de_Bases_de_Dados.csv  (este arquivo)
├── GUIA_DOWNLOAD_ANATEL.md          (este guia)
├── Cobertura_Telefonia_Movel.csv    (exemplo de dataset baixado)
├── Estacoes_Banda_Larga_Fixa.csv    (exemplo de dataset baixado)
└── processados/                     (arquivos já processados)
```

## 🚀 Próximos Passos
1. Baixe pelo menos 2-3 datasets da lista acima
2. Coloque os arquivos CSV na pasta `data/manual/`
3. Execute: `python data_pipeline/connectors/anatel_smart_connector.py --process`
