# ANATEL Smart Connector

Sistema inteligente de gerenciamento e processamento de datasets da ANATEL (Agência Nacional de Telecomunicações) para mapeamento de conectividade rural.

## Visão Geral

O ANATEL Smart Connector é composto por dois módulos principais:

1. **AnatelStaticConnector**: Processa arquivos CSV manuais
2. **AnatelSmartConnector**: Gerencia datasets usando inventário com priorização automática

## Arquitetura

```
data/manual/                          # Arquivos manuais e inventário
  ├── Inventario_de_Bases_de_Dados.csv
  ├── GUIA_DOWNLOAD_ANATEL.md
  └── *.csv                           # Datasets baixados

data/bronze/anatel/                   # Dados processados (formato JSON)
  ├── *_YYYYMMDD_HHMMSS.json
  ├── relatorio_consolidado_*.json
  └── resumo_processamento_*.txt
```

## Categorias de Datasets

### Alta Prioridade (Infraestrutura Física)
- Cobertura de telefonia móvel
- Backhaul em municípios
- Estações de telecomunicações (banda larga, móvel, TV, rádio, satélite)
- Satélites autorizados
- População coberta
- Escolas rurais conectadas
- Municípios com área rural atendida

### Média Prioridade (Acessos e Qualidade)
- Acessos de banda larga
- Velocidade contratada
- Indicadores de qualidade

### Baixa Prioridade (Outros)
- Arrecadação
- Reclamações
- Portabilidade numérica

## Uso

### Mostrar Datasets Prioritários

```bash
python data_pipeline/connectors/anatel_smart_connector.py --show-priority
```

Exibe os datasets de alta prioridade disponíveis no inventário.

### Gerar Guia de Download

```bash
python data_pipeline/connectors/anatel_smart_connector.py --generate-guide
```

Cria um guia em Markdown (`data/manual/GUIA_DOWNLOAD_ANATEL.md`) com instruções detalhadas para download dos datasets prioritários.

### Processar Arquivos Manuais

```bash
python data_pipeline/connectors/anatel_smart_connector.py --process
```

Processa todos os arquivos CSV em `data/manual/` e gera:
- Arquivos JSON no formato bronze
- Relatório consolidado (JSON)
- Resumo de processamento (TXT)

### Download Automático (Experimental)

```bash
python data_pipeline/connectors/anatel_smart_connector.py --download ITEM_ID
```

Tenta fazer download automático de um dataset pelo ID do inventário.

## Exemplo de Workflow

1. **Listar datasets prioritários:**
   ```bash
   python data_pipeline/connectors/anatel_smart_connector.py --show-priority
   ```

2. **Gerar guia de download:**
   ```bash
   python data_pipeline/connectors/anatel_smart_connector.py --generate-guide
   ```

3. **Baixar datasets manualmente** (seguindo o guia):
   - Acesse os links fornecidos no guia
   - Baixe os arquivos CSV
   - Coloque em `data/manual/`

4. **Processar datasets:**
   ```bash
   python data_pipeline/connectors/anatel_smart_connector.py --process
   ```

## Formato de Saída (Bronze)

Cada arquivo CSV processado gera um arquivo JSON com a seguinte estrutura:

```json
{
  "metadata": {
    "source_file": "nome_do_arquivo.csv",
    "file_hash": "abc123...",
    "processing_timestamp": "2026-01-24T18:00:00",
    "total_rows": 1000,
    "columns": ["coluna1", "coluna2", ...],
    "separator": ";",
    "encoding": "utf-8"
  },
  "data": [
    {"coluna1": "valor1", "coluna2": "valor2"},
    ...
  ]
}
```

## Relatório Consolidado

Após o processamento, é gerado um relatório em dois formatos:

### JSON (`relatorio_consolidado_*.json`)
```json
{
  "metadata": {
    "data_execucao": "2026-01-24T18:00:00",
    "inventario_utilizado": "Inventario_de_Bases_de_Dados.csv",
    "total_datasets_inventario": 22
  },
  "processamento": {
    "total_arquivos_processados": 5,
    "sucessos": 5,
    "erros": 0
  },
  "datasets_prioritarios_disponiveis": [...]
}
```

### TXT (`resumo_processamento_*.txt`)
Resumo legível para humanos do processamento.

## Testes

Execute os testes:

```bash
python -m pytest tests/test_anatel_connectors.py -v
```

Cobertura de testes:
- ✅ Inicialização de conectores
- ✅ Busca de arquivos CSV
- ✅ Processamento de arquivos individuais
- ✅ Processamento em lote
- ✅ Carregamento de inventário
- ✅ Classificação de datasets
- ✅ Exibição de datasets prioritários
- ✅ Geração de guia de download
- ✅ Geração de relatórios consolidados
- ✅ Comportamento sem inventário

## Dependências

```
pandas>=2.0.0
requests>=2.31.0
```

## Próximos Passos

1. Integração com pipeline de dados existente
2. Download automático completo de todos os datasets
3. Agendamento automático de atualizações
4. Notificações de novos datasets disponíveis
5. Validação de esquema de dados
6. Transformações específicas por tipo de dataset

## Contribuindo

Para adicionar novos datasets ou modificar prioridades, edite:
- `data/manual/Inventario_de_Bases_de_Dados.csv` (adicionar novos datasets)
- `DATASET_CATEGORIES` em `anatel_smart_connector.py` (modificar keywords de classificação)

## Licença

Este componente faz parte do projeto Rural Connectivity Mapper 2026.
