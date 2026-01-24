"""
Conector para dados estáticos da ANATEL (download manual de CSV).
Assume que o usuário baixou os arquivos do Portal de Dados Abertos.
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import hashlib
import logging
from typing import Dict, List, Optional
import shutil

# Configuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnatelStaticConnector:
    """
    Processa arquivos CSV baixados manualmente do portal da ANATEL.
    """
    
    # Mapeamento de datasets conhecidos da ANATEL e seus schemas esperados
    KNOWN_DATASETS = {
        'backhaul': {
            'expected_columns': ['id', 'municipio', 'uf', 'operadora', 'latitude', 'longitude', 'frequencia', 'capacidade_mbps'],
            'description': 'Infraestrutura de transporte (backhaul)'
        },
        'estacoes': {
            'expected_columns': ['id', 'municipio', 'uf', 'operadora', 'tecnologia', 'latitude', 'longitude'],
            'description': 'Estações de telecomunicações'
        },
        'acesso_fixo': {
            'expected_columns': ['municipio', 'uf', 'quantidade', 'velocidade', 'tecnologia'],
            'description': 'Acessos fixos de banda larga'
        }
    }
    
    def __init__(self, manual_dir: Path = Path("data/manual")):
        self.manual_dir = manual_dir
        self.manual_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path("data/bronze/anatel")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def discover_new_files(self) -> List[Path]:
        """Descobre novos arquivos CSV na pasta manual."""
        csv_files = list(self.manual_dir.glob("*.csv")) + list(self.manual_dir.glob("*.CSV"))
        logger.info(f"Encontrados {len(csv_files)} arquivos CSV em {self.manual_dir}")
        return csv_files
    
    def infer_dataset_type(self, df: pd.DataFrame, filename: str) -> str:
        """Infere o tipo de dataset com base nas colunas e nome do arquivo."""
        filename_lower = filename.lower()
        
        # Primeiro, tenta inferir pelo nome do arquivo
        if 'backhaul' in filename_lower:
            return 'backhaul'
        elif 'estacao' in filename_lower or 'estação' in filename_lower:
            return 'estacoes'
        elif 'acesso' in filename_lower and 'fixo' in filename_lower:
            return 'acesso_fixo'
        
        # Se não der pelo nome, tenta pelas colunas
        for ds_type, config in self.KNOWN_DATASETS.items():
            if all(col in df.columns for col in config['expected_columns'][:3]):  # Pelo menos 3 colunas essenciais
                return ds_type
        
        return 'desconhecido'
    
    def validate_and_clean(self, df: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
        """Aplica validação e limpeza específica para cada tipo de dataset."""
        
        # Cópia para não modificar o original
        df_clean = df.copy()
        
        # 1. Limpeza básica de strings
        string_cols = df_clean.select_dtypes(include=['object']).columns
        for col in string_cols:
            df_clean[col] = df_clean[col].astype(str).str.strip().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('ascii')
        
        # 2. Validações específicas por tipo
        if dataset_type == 'backhaul':
            # Garantir coordenadas
            if 'latitude' in df_clean.columns and 'longitude' in df_clean.columns:
                df_clean['latitude'] = pd.to_numeric(df_clean['latitude'], errors='coerce')
                df_clean['longitude'] = pd.to_numeric(df_clean['longitude'], errors='coerce')
                # Remover coordenadas inválidas
                df_clean = df_clean.dropna(subset=['latitude', 'longitude'])
                # Filtrar para Brasil
                df_clean = df_clean[
                    (df_clean['latitude'].between(-33.75, 5.27)) & 
                    (df_clean['longitude'].between(-73.99, -34.79))
                ]
            
            # Converter capacidade para numérico
            if 'capacidade_mbps' in df_clean.columns:
                df_clean['capacidade_mbps'] = pd.to_numeric(df_clean['capacidade_mbps'], errors='coerce')
        
        elif dataset_type == 'estacoes':
            # Adicionar geohash para agrupamento espacial futuro
            if all(col in df_clean.columns for col in ['latitude', 'longitude']):
                df_clean['geohash'] = df_clean.apply(
                    lambda row: self._compute_geohash(row['latitude'], row['longitude'], precision=7), 
                    axis=1
                )
        
        # 3. Adicionar metadados de processamento
        df_clean['_processamento_data'] = datetime.now().isoformat()
        df_clean['_dataset_tipo'] = dataset_type
        df_clean['_confidence_score'] = 0.9  # Alto para dados oficiais
        
        return df_clean
    
    def _compute_geohash(self, lat: float, lon: float, precision: int = 7) -> str:
        """Calcula geohash para agrupamento espacial (simplificado para exemplo)."""
        try:
            # Em produção, usar biblioteca como geohash2
            import geohash2
            return geohash2.encode(lat, lon, precision)
        except ImportError:
            # Fallback simplificado
            return f"{lat:.4f},{lon:.4f}"
    
    def process_file(self, filepath: Path) -> Dict:
        """Processa um único arquivo CSV."""
        logger.info(f"Processando: {filepath.name}")
        
        try:
            # Ler CSV com detecção automática de encoding (comum em dados BR)
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Não foi possível decodificar {filepath.name} com encodings comuns")
            
            # Inferir tipo de dataset
            dataset_type = self.infer_dataset_type(df, filepath.name)
            logger.info(f"Dataset inferido: {dataset_type}")
            
            # Validar e limpar
            df_clean = self.validate_and_clean(df, dataset_type)
            
            # Gerar hash do conteúdo para versionamento
            content_hash = hashlib.md5(pd.util.hash_pandas_object(df_clean).values).hexdigest()[:8]
            
            # Nome do arquivo de saída
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"anatel_{dataset_type}_{timestamp}_{content_hash}.parquet"
            output_path = self.output_dir / output_filename
            
            # Salvar como Parquet (eficiente e preserva tipos)
            df_clean.to_parquet(output_path, index=False)
            
            # Estatísticas
            stats = {
                'arquivo_origem': filepath.name,
                'dataset_tipo': dataset_type,
                'registros_processados': len(df_clean),
                'registros_originais': len(df),
                'hash_conteudo': content_hash,
                'caminho_saida': str(output_path),
                'data_processamento': timestamp,
                'colunas': list(df_clean.columns)
            }
            
            # Mover arquivo original para subpasta "processados"
            processed_dir = self.manual_dir / "processados"
            processed_dir.mkdir(exist_ok=True)
            shutil.move(filepath, processed_dir / filepath.name)
            
            logger.info(f"✅ Processado: {len(df_clean)} registros salvos em {output_path}")
            return {'status': 'success', 'stats': stats}
            
        except Exception as e:
            logger.error(f"❌ Falha ao processar {filepath.name}: {e}")
            return {'status': 'error', 'file': filepath.name, 'error': str(e)}
    
    def run(self) -> List[Dict]:
        """Executa o pipeline completo para todos os novos arquivos."""
        logger.info("=" * 50)
        logger.info("Iniciando processamento de dados estáticos da ANATEL")
        logger.info("=" * 50)
        
        files = self.discover_new_files()
        if not files:
            logger.warning(f"Nenhum novo arquivo CSV encontrado em {self.manual_dir}")
            logger.info(f"👉 Instruções: Baixe os CSVs do Portal de Dados Abertos e cole em {self.manual_dir.absolute()}")
            return []
        
        results = []
        for filepath in files:
            result = self.process_file(filepath)
            results.append(result)
        
        # Gerar relatório de execução
        self._generate_report(results)
        return results
    
    def _generate_report(self, results: List[Dict]):
        """Gera um relatório JSON do processamento."""
        report = {
            'data_execucao': datetime.now().isoformat(),
            'total_arquivos': len(results),
            'sucessos': sum(1 for r in results if r['status'] == 'success'),
            'erros': sum(1 for r in results if r['status'] == 'error'),
            'detalhes': results
        }
        
        report_path = self.output_dir / f"relatorio_processamento_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Relatório gerado: {report_path}")

# ----------------------------------------------------
# INSTRUÇÕES PARA O USUÁRIO
# ----------------------------------------------------
def print_instructions():
    """Exibe instruções claras para o usuário."""
    print("\n" + "=" * 60)
    print("📥 INSTRUÇÕES: COMO BAIXAR OS DADOS DA ANATEL")
    print("=" * 60)
    print("1. Acesse: https://dadosabertos.anatel.gov.br/")
    print("2. Busque por:")
    print("   • 'Backhaul' (infraestrutura de transporte)")
    print("   • 'Estações de Telecomunicações'")
    print("   • 'Acessos Fixos' (banda larga fixa)")
    print("3. Faça download dos CSVs disponíveis")
    print("4. Cole os arquivos .csv na pasta:")
    print(f"   {Path('data/manual').absolute()}")
    print("5. Execute: python anatel_static_connector.py")
    print("=" * 60)

if __name__ == "__main__":
    # Mostrar instruções
    print_instructions()
    
    # Executar o processamento
    connector = AnatelStaticConnector()
    results = connector.run()
    
    # Resumo final
    if results:
        success_count = sum(1 for r in results if r['status'] == 'success')
        print(f"\n🎯 Processamento concluído: {success_count}/{len(results)} arquivos processados com sucesso!")
        print("   Os dados estão disponíveis em: data/bronze/anatel/")
        print("   Próximo passo: Execute o fusion_engine.py para unificar com outras fontes.")
    else:
        print("\n⚠️  Nenhum arquivo para processar.")
        print("   Cole os CSVs na pasta 'data/manual/' e execute novamente.")
