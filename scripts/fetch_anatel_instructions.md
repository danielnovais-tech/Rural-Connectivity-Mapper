# Guia: Como Baixar Dados da ANATEL

Este guia explica como fazer o download manual de dados de telecomunicações da ANATEL (Agência Nacional de Telecomunicações) para uso no Rural Connectivity Mapper.

## 📥 Processo de Download

### Passo 1: Acessar o Portal de Dados Abertos

Acesse o portal oficial da ANATEL:
- **URL**: https://dadosabertos.anatel.gov.br/

### Passo 2: Buscar os Datasets Necessários

Recomendamos buscar pelos seguintes datasets:

#### 1. **Infraestrutura de Backhaul**
- Buscar por: "Backhaul" ou "Infraestrutura de Transporte"
- Descrição: Dados sobre a infraestrutura de transporte de dados (backhaul)
- Colunas esperadas: id, município, UF, operadora, latitude, longitude, frequência, capacidade_mbps

#### 2. **Estações de Telecomunicações**
- Buscar por: "Estações de Telecomunicações" ou "ERB" (Estação Rádio Base)
- Descrição: Dados sobre estações de rádio base e infraestrutura de telecomunicações
- Colunas esperadas: id, município, UF, operadora, tecnologia, latitude, longitude

#### 3. **Acessos Fixos de Banda Larga**
- Buscar por: "Acessos Fixos" ou "Banda Larga Fixa"
- Descrição: Dados sobre acessos de banda larga fixa por município
- Colunas esperadas: município, UF, quantidade, velocidade, tecnologia

### Passo 3: Fazer Download dos Arquivos CSV

1. Clique no dataset desejado
2. Na página do dataset, localize o botão de **Download** ou **Explorar**
3. Escolha o formato **CSV** (se houver outras opções)
4. Salve o arquivo no seu computador

### Passo 4: Organizar os Arquivos

1. Navegue até a pasta do projeto: `Rural-Connectivity-Mapper-2026`
2. Copie os arquivos CSV baixados para a pasta: **`data/manual/`**
3. Os nomes dos arquivos podem seguir o padrão (opcional):
   - `Anatel_Backhaul_2024-10.csv`
   - `Anatel_Estacoes_2024-10.csv`
   - `Anatel_Acesso_Fixo_2024-10.csv`

### Passo 5: Executar o Processamento

Execute o conector estático para processar os arquivos:

```bash
python data_pipeline/connectors/anatel_static_connector.py
```

Ou, se estiver em um diretório diferente:

```bash
cd /caminho/para/Rural-Connectivity-Mapper-2026
python data_pipeline/connectors/anatel_static_connector.py
```

## 📊 O Que Acontece Depois?

O conector irá:

1. ✅ **Descobrir** os arquivos CSV na pasta `data/manual/`
2. ✅ **Inferir** o tipo de dataset baseado no nome do arquivo e colunas
3. ✅ **Validar e limpar** os dados (remover valores inválidos, normalizar strings)
4. ✅ **Processar** coordenadas geográficas (validar que estão no Brasil)
5. ✅ **Salvar** os dados processados em formato Parquet na pasta `data/bronze/anatel/`
6. ✅ **Mover** os arquivos originais para `data/manual/processados/`
7. ✅ **Gerar** um relatório JSON com estatísticas do processamento

## 🗂️ Estrutura de Diretórios

```
data/
├── manual/                    # Cola os CSVs aqui
│   ├── processados/          # Arquivos já processados (movidos automaticamente)
│   └── (seus CSVs vão aqui)
├── bronze/anatel/            # Dados processados em Parquet
│   ├── anatel_backhaul_20241024_123456_abc123.parquet
│   └── relatorio_processamento_20241024_1234.json
├── silver/                   # Dados unificados (próxima etapa)
└── gold/                     # Indicadores finais (última etapa)
```

## 🔍 Verificação de Dados

Para verificar se os dados foram processados corretamente:

```python
import pandas as pd
from pathlib import Path

# Listar arquivos processados
bronze_dir = Path("data/bronze/anatel")
parquet_files = list(bronze_dir.glob("*.parquet"))
print(f"Arquivos processados: {len(parquet_files)}")

# Ler um arquivo para inspeção
if parquet_files:
    df = pd.read_parquet(parquet_files[0])
    print(f"\nPrimeiras linhas do dataset:")
    print(df.head())
    print(f"\nColunas: {list(df.columns)}")
    print(f"\nTotal de registros: {len(df)}")
```

## ⚠️ Observações Importantes

1. **Encoding**: O conector tenta automaticamente detectar o encoding dos arquivos CSV (UTF-8, Latin-1, CP1252)
2. **Validação Geográfica**: Coordenadas fora do território brasileiro são filtradas
3. **Backup**: Os arquivos originais são preservados na pasta `processados/`
4. **Formato**: Os dados são salvos em Parquet para melhor performance e preservação de tipos

## 🆘 Problemas Comuns

### "Nenhum arquivo encontrado"
- Certifique-se de que os arquivos CSV estão na pasta `data/manual/`
- Verifique se a extensão é `.csv` ou `.CSV`

### "Erro ao decodificar arquivo"
- O arquivo pode estar corrompido
- Tente abrir o CSV em um editor de texto para verificar o conteúdo

### "Dataset tipo 'desconhecido'"
- O arquivo não corresponde aos schemas conhecidos
- Verifique se as colunas do CSV correspondem aos campos esperados

## 📞 Suporte

Para mais informações sobre os dados da ANATEL:
- Portal: https://dadosabertos.anatel.gov.br/
- Documentação: https://www.anatel.gov.br/dadosabertos/

Para problemas com o processamento, abra uma issue no repositório do projeto.
