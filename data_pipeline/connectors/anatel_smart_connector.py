"""
Conector Inteligente para Dados da ANATEL.
Utiliza o inventário de bases de dados para identificar, priorizar e processar datasets.
"""
import io
import json
import logging
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

# Adicionar diretório raiz ao path para importações
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnatelSmartConnector:
    """
    Conector que utiliza o inventário para gerenciar múltiplos datasets da ANATEL.
    """

    # Categorias e prioridades baseadas na análise do inventário
    DATASET_CATEGORIES = {
        'infraestrutura_alta': {
            'keywords': ['cobertura', 'backhaul', 'estações', 'estacoes', 'satélites',
                        'satelites', 'escolas rurais', 'população coberta', 'rural'],
            'priority': 1,
            'description': 'Dados de infraestrutura física e cobertura geográfica'
        },
        'infraestrutura_media': {
            'keywords': ['acessos', 'velocidade', 'qualidade', 'município'],
            'priority': 2,
            'description': 'Dados de acessos e qualidade de serviço'
        },
        'outros': {
            'keywords': [],
            'priority': 3,
            'description': 'Outros datasets (arrecadação, reclamações, etc.)'
        }
    }

    def __init__(self, inventory_path: Path | None = None):
        self.inventory_path = inventory_path or Path("data/manual/Inventario_de_Bases_de_Dados.csv")
        self.manual_dir = Path("data/manual")
        self.manual_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path("data/bronze/anatel")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Carregar inventário se existir
        self.inventory = None
        if self.inventory_path.exists():
            self.load_inventory()

    def load_inventory(self):
        """Carrega e analisa o inventário de bases de dados."""
        try:
            # O inventário usa ponto e vírgula como separador
            self.inventory = pd.read_csv(self.inventory_path, sep=';', encoding='utf-8')
            logger.info(f"Inventário carregado: {len(self.inventory)} datasets")

            # Classificar cada dataset por categoria
            self.inventory['categoria'] = self.inventory['Descrição da Base de Dados'].apply(
                self._classify_dataset
            )

            # Ordenar por prioridade
            category_priority = {cat: config['priority'] for cat, config in self.DATASET_CATEGORIES.items()}
            self.inventory['prioridade'] = self.inventory['categoria'].map(category_priority)
            self.inventory = self.inventory.sort_values('prioridade')

        except Exception as e:
            logger.error(f"Erro ao carregar inventário: {e}")
            self.inventory = None

    def _classify_dataset(self, description: str) -> str:
        """Classifica um dataset com base na descrição."""
        desc_lower = description.lower()

        for category, config in self.DATASET_CATEGORIES.items():
            if category == 'outros':
                continue
            for keyword in config['keywords']:
                if keyword in desc_lower:
                    return category

        return 'outros'

    def show_priority_datasets(self, limit: int = 15):
        """Exibe os datasets de maior prioridade para o usuário."""
        if self.inventory is None:
            logger.warning("Inventário não carregado.")
            return

        print("\n" + "="*80)
        print("🎯 DATASETS DE ALTA PRIORIDADE PARA MAPEAMENTO DE CONECTIVIDADE RURAL")
        print("="*80)

        high_priority = self.inventory[self.inventory['categoria'] == 'infraestrutura_alta']

        for _idx, row in high_priority.head(limit).iterrows():
            print(f"\n#{row['Item']} {row['Nome da Base de Dados']}")
            print(f"   Descrição: {row['Descrição da Base de Dados'][:100]}...")
            link_display = row['Link dados.gov.br'] if pd.notna(row['Link dados.gov.br']) else 'N/A'
            print(f"   Disponível em: {link_display}")
            print(f"   Periodicidade: {row['Periodicidade de Atualização']}")
            print(f"   Categoria: {row['categoria'].upper()}")

        print(f"\n📊 Total de datasets de infraestrutura (alta prioridade): {len(high_priority)}")
        print("="*80)

    def generate_download_guide(self):
        """Gera um guia passo a passo para download dos datasets prioritários."""
        if self.inventory is None:
            return

        high_priority = self.inventory[self.inventory['categoria'] == 'infraestrutura_alta']

        guide_path = self.manual_dir / "GUIA_DOWNLOAD_ANATEL.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write("# Guia para Download de Datasets Prioritários da ANATEL\n\n")
            f.write("**Gerado automaticamente em:** " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
            f.write("## 🎯 Datasets Mais Importantes para Conectividade Rural\n\n")

            for _, row in high_priority.iterrows():
                f.write(f"### {row['Item']}. {row['Nome da Base de Dados']}\n")
                f.write(f"- **Descrição:** {row['Descrição da Base de Dados']}\n")
                f.write("- **Prioridade:** ALTA (Infraestrutura física)\n")
                f.write(f"- **Atualização:** {row['Periodicidade de Atualização']}\n")

                if pd.notna(row['Link dados.gov.br']):
                    f.write(f"- **Link direto:** [{row['Link dados.gov.br']}]({row['Link dados.gov.br']})\n")
                    f.write("- **Instruções:** Acesse o link acima, procure pela opção de download "
                            "(geralmente CSV ou ZIP)\n")
                elif pd.notna(row['Link Painéis de Dados da Anatel']):
                    f.write(f"- **Painel da ANATEL:** {row['Link Painéis de Dados da Anatel']}\n")
                    f.write("- **Instruções:** Acesse o painel acima, procure pela opção de download "
                            "(geralmente CSV ou ZIP)\n")
                else:
                    f.write("- **Instruções:** Dataset sem link direto. Verifique o site da ANATEL ou use fontes alternativas.\n")

                dataset_name = row['Nome da Base de Dados'].replace(' ', '_').replace('/', '_')
                f.write(f"- **Salve como:** `{dataset_name}_{{DATA}}.csv`\n")
                f.write(f"- **Coloque em:** `{self.manual_dir.absolute()}/`\n\n")

            f.write("## 📁 Estrutura de Pastas Recomendada\n")
            f.write("```\n")
            f.write(f"{self.manual_dir.absolute()}/\n")
            f.write("├── Inventario_de_Bases_de_Dados.csv  (este arquivo)\n")
            f.write("├── GUIA_DOWNLOAD_ANATEL.md          (este guia)\n")
            f.write("├── Cobertura_Telefonia_Movel.csv    (exemplo de dataset baixado)\n")
            f.write("├── Estacoes_Banda_Larga_Fixa.csv    (exemplo de dataset baixado)\n")
            f.write("└── processados/                     (arquivos já processados)\n")
            f.write("```\n\n")

            f.write("## 🚀 Próximos Passos\n")
            f.write("1. Baixe pelo menos 2-3 datasets da lista acima\n")
            f.write("2. Coloque os arquivos CSV na pasta `data/manual/`\n")
            f.write("3. Execute: `python data_pipeline/connectors/anatel_smart_connector.py --process`\n")

        logger.info(f"Guia de download gerado: {guide_path}")
        return guide_path

    def auto_download_dataset(self, dataset_url: str, dataset_name: str) -> Path | None:
        """
        Tenta fazer download automático de um dataset a partir da URL.
        Funciona para links diretos a arquivos .csv, .zip, etc.
        """
        try:
            logger.info(f"Tentando download automático: {dataset_name}")

            response = requests.get(dataset_url, timeout=30)
            response.raise_for_status()

            # Determinar tipo de arquivo pela URL ou headers
            content_type = response.headers.get('content-type', '')
            parsed_url = urlparse(dataset_url)
            filename = parsed_url.path.split('/')[-1]

            if not filename:
                filename = f"{dataset_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"

            output_path = self.manual_dir / filename

            # Se for ZIP, extrair
            if 'zip' in content_type or filename.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                    # Extrair todos os arquivos
                    zip_ref.extractall(self.manual_dir)
                    extracted_files = zip_ref.namelist()
                    logger.info(f"Arquivo ZIP extraído. Arquivos: {extracted_files}")
                    return self.manual_dir / extracted_files[0] if extracted_files else None
            else:
                # Outros arquivos (CSV, JSON, etc.)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Download concluído: {output_path}")
                return output_path

        except Exception as e:
            logger.warning(f"Download automático falhou para {dataset_url}: {e}")
            return None

    def process_all_manual_files(self):
        """Processa todos os arquivos CSV na pasta manual."""
        # Import here to avoid circular dependency issues
        from data_pipeline.connectors.anatel_static_connector import AnatelStaticConnector

        static_connector = AnatelStaticConnector(self.manual_dir)
        results = static_connector.run()

        # Gerar relatório consolidado
        self._generate_consolidated_report(results)
        return results

    def _generate_consolidated_report(self, processing_results: list[dict]):
        """Gera um relatório consolidado do processamento."""
        report = {
            'metadata': {
                'data_execucao': datetime.now().isoformat(),
                'inventario_utilizado': self.inventory_path.name if self.inventory is not None else None,
                'total_datasets_inventario': len(self.inventory) if self.inventory is not None else 0
            },
            'processamento': {
                'total_arquivos_processados': len(processing_results),
                'sucessos': sum(1 for r in processing_results if r.get('status') == 'success'),
                'erros': sum(1 for r in processing_results if r.get('status') == 'error')
            },
            'datasets_prioritarios_disponiveis': []
        }

        # Listar datasets prioritários disponíveis no inventário
        if self.inventory is not None:
            high_priority = self.inventory[self.inventory['categoria'] == 'infraestrutura_alta']
            # Convert to dict and replace NaN with None
            datasets_dict = high_priority[['Item', 'Nome da Base de Dados', 'Link dados.gov.br']].to_dict('records')
            # Replace NaN values with None
            for dataset in datasets_dict:
                for key, value in dataset.items():
                    if pd.isna(value):
                        dataset[key] = None
            report['datasets_prioritarios_disponiveis'] = datasets_dict

        report_path = self.output_dir / f"relatorio_consolidado_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 Relatório consolidado gerado: {report_path}")

        # Também gerar uma versão em texto simples para leitura rápida
        txt_report = self.output_dir / f"resumo_processamento_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(txt_report, 'w', encoding='utf-8') as f:
            f.write("RESUMO DO PROCESSAMENTO ANATEL\n")
            f.write("="*50 + "\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Arquivos processados: {report['processamento']['total_arquivos_processados']}\n")
            f.write(f"Sucessos: {report['processamento']['sucessos']}\n")
            f.write(f"Erros: {report['processamento']['erros']}\n\n")

            if report['datasets_prioritarios_disponiveis']:
                f.write("DATASETS PRIORITÁRIOS DISPONÍVEIS (não baixados):\n")
                for ds in report['datasets_prioritarios_disponiveis'][:10]:  # Mostrar só os 10 primeiros
                    f.write(f"  #{ds['Item']} {ds['Nome da Base de Dados']}\n")
                    if not pd.isna(ds['Link dados.gov.br']):
                        f.write(f"     Link: {ds['Link dados.gov.br']}\n")

        return report_path

# ----------------------------------------------------
# INTERFACE DE LINHA DE COMANDO
# ----------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Conector Inteligente ANATEL')
    parser.add_argument('--inventory', default='data/manual/Inventario_de_Bases_de_Dados.csv',
                       help='Caminho para o arquivo de inventário')
    parser.add_argument('--show-priority', action='store_true',
                       help='Mostrar datasets de alta prioridade')
    parser.add_argument('--generate-guide', action='store_true',
                       help='Gerar guia de download em Markdown')
    parser.add_argument('--process', action='store_true',
                       help='Processar todos os arquivos na pasta manual')
    parser.add_argument('--download', metavar='ITEM_ID',
                       help='Tentar download automático de um dataset pelo ID do inventário')

    args = parser.parse_args()

    connector = AnatelSmartConnector(Path(args.inventory))

    if args.show_priority:
        connector.show_priority_datasets()

    if args.generate_guide:
        guide_path = connector.generate_download_guide()
        print(f"\n✅ Guia gerado: {guide_path}")
        print("👉 Siga as instruções no guia para baixar os datasets mais importantes.")

    if args.download:
        # Buscar o dataset no inventário pelo ID
        if connector.inventory is not None:
            dataset = connector.inventory[connector.inventory['Item'] == int(args.download)]
            if not dataset.empty:
                url = dataset.iloc[0]['Link dados.gov.br']
                name = dataset.iloc[0]['Nome da Base de Dados']
                if pd.notna(url):
                    result = connector.auto_download_dataset(url, name)
                    if result:
                        print(f"✅ Download concluído: {result}")
                    else:
                        print("❌ Download falhou. Faça manualmente seguindo o guia.")
                else:
                    print(f"❌ Dataset #{args.download} não possui link direto.")
            else:
                print(f"❌ Dataset com ID #{args.download} não encontrado no inventário.")

    if args.process:
        print("\n" + "="*50)
        print("Iniciando processamento de arquivos manuais...")
        print("="*50)
        results = connector.process_all_manual_files()

        if results:
            success_count = sum(1 for r in results if r.get('status') == 'success')
            print(f"\n🎯 Processamento concluído: {success_count}/{len(results)} arquivos processados!")
            print("   Os dados estão disponíveis em: data/bronze/anatel/")
            print("   Próximo passo: Execute o fusion_engine.py para unificar com outras fontes.")
        else:
            print("\n⚠️  Nenhum arquivo para processar.")
            print("   Use --generate-guide para criar um guia de download.")
            print("   Baixe os datasets e execute novamente com --process")

if __name__ == "__main__":
    main()
