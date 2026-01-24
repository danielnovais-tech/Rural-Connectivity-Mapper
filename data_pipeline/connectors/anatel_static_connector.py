"""
Conector Estático para Dados da ANATEL.
Processa arquivos CSV manuais da pasta data/manual e converte para formato bronze.
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import hashlib
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnatelStaticConnector:
    """
    Conector que processa arquivos CSV manuais da ANATEL.
    """
    
    def __init__(self, manual_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        self.manual_dir = manual_dir or Path("data/manual")
        self.output_dir = output_dir or Path("data/bronze/anatel")
        
        # Criar diretórios se não existirem
        self.manual_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def find_csv_files(self) -> List[Path]:
        """Encontra todos os arquivos CSV na pasta manual."""
        csv_files = list(self.manual_dir.glob("*.csv"))
        logger.info(f"Encontrados {len(csv_files)} arquivos CSV em {self.manual_dir}")
        return csv_files
    
    def process_csv_file(self, csv_path: Path) -> Dict:
        """Processa um arquivo CSV individual."""
        try:
            logger.info(f"Processando: {csv_path.name}")
            
            # Tentar diferentes separadores e encodings
            df = None
            for sep in [';', ',', '\t']:
                for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                    try:
                        df = pd.read_csv(csv_path, sep=sep, encoding=encoding)
                        if len(df.columns) > 1:  # Verificar se separador funcionou
                            break
                    except Exception:
                        continue
                if df is not None and len(df.columns) > 1:
                    break
            
            if df is None or len(df.columns) <= 1:
                logger.error(f"Não foi possível ler o arquivo {csv_path.name}")
                return {
                    'status': 'error',
                    'file': csv_path.name,
                    'error': 'Formato de arquivo não suportado'
                }
            
            # Gerar hash do arquivo para rastreamento
            file_hash = self._generate_file_hash(csv_path)
            
            # Metadata do processamento
            metadata = {
                'source_file': csv_path.name,
                'file_hash': file_hash,
                'processing_timestamp': datetime.now().isoformat(),
                'total_rows': len(df),
                'columns': list(df.columns),
                'separator': sep,
                'encoding': encoding
            }
            
            # Salvar no formato bronze
            output_filename = f"{csv_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = self.output_dir / output_filename
            
            # Converter DataFrame para formato JSON
            bronze_data = {
                'metadata': metadata,
                'data': df.to_dict(orient='records')
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(bronze_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"✓ Arquivo processado: {output_path}")
            
            return {
                'status': 'success',
                'file': csv_path.name,
                'output': output_path.name,
                'rows': len(df),
                'columns': len(df.columns)
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar {csv_path.name}: {e}")
            return {
                'status': 'error',
                'file': csv_path.name,
                'error': str(e)
            }
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """Gera hash SHA256 do arquivo."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()[:16]
    
    def run(self) -> List[Dict]:
        """Executa o processamento de todos os arquivos CSV."""
        csv_files = self.find_csv_files()
        
        if not csv_files:
            logger.warning("Nenhum arquivo CSV encontrado para processar.")
            return []
        
        results = []
        for csv_file in csv_files:
            result = self.process_csv_file(csv_file)
            results.append(result)
        
        # Resumo do processamento
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Processamento concluído:")
        logger.info(f"  Sucessos: {success_count}")
        logger.info(f"  Erros: {error_count}")
        logger.info(f"{'='*50}")
        
        return results


if __name__ == "__main__":
    connector = AnatelStaticConnector()
    connector.run()
