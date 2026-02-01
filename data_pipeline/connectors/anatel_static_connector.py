"""
Connector for ANATEL static datasets (manual CSV download).

This connector expects the user to place downloaded ANATEL CSV files into a
"manual" directory, then converts them into Parquet in an output directory.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

try:
    import geohash2

    _GEOHASH_AVAILABLE = True
except ImportError:
    _GEOHASH_AVAILABLE = False


logger = logging.getLogger(__name__)


class ANATELStaticConnector:
    """Processes manually downloaded ANATEL CSVs and writes Parquet outputs."""

    KNOWN_DATASETS: Dict[str, Dict[str, object]] = {
        "backhaul": {
            "expected_columns": [
                "id",
                "municipio",
                "uf",
                "operadora",
                "latitude",
                "longitude",
                "frequencia",
                "capacidade_mbps",
            ],
            "description": "Infraestrutura de transporte (backhaul)",
        },
        "estacoes": {
            "expected_columns": [
                "id",
                "municipio",
                "uf",
                "operadora",
                "tecnologia",
                "latitude",
                "longitude",
            ],
            "description": "Estações de telecomunicações",
        },
        "acesso_fixo": {
            "expected_columns": [
                "municipio",
                "uf",
                "quantidade",
                "velocidade",
                "tecnologia",
            ],
            "description": "Acessos fixos de banda larga",
        },
    }

    def __init__(self, manual_dir: Path = Path("data/manual"), output_dir: Optional[Path] = None):
        self.manual_dir = Path(manual_dir)
        self.manual_dir.mkdir(parents=True, exist_ok=True)

        # Keep outputs close to the manual directory when running tests.
        self.output_dir = Path(output_dir) if output_dir is not None else (self.manual_dir.parent / "bronze" / "anatel")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def discover_new_files(self) -> List[Path]:
        """Finds new CSV files in the manual directory."""
        csv_files = list(self.manual_dir.glob("*.csv")) + list(self.manual_dir.glob("*.CSV"))

        # On Windows (case-insensitive FS) the same file can match both patterns.
        unique_files: List[Path] = []
        seen: set[str] = set()
        for path in csv_files:
            try:
                key = str(path.resolve()).lower()
            except OSError:
                key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            unique_files.append(path)

        logger.info("Found %s CSV files in %s", len(unique_files), self.manual_dir)
        return unique_files

    def infer_dataset_type(self, df: pd.DataFrame, filename: str) -> str:
        """Infer dataset type based on filename and available columns."""
        filename_lower = filename.lower()

        if "backhaul" in filename_lower:
            return "backhaul"
        if "estacao" in filename_lower or "estação" in filename_lower:
            return "estacoes"
        if "acesso" in filename_lower and "fixo" in filename_lower:
            return "acesso_fixo"

        for dataset_type, config in self.KNOWN_DATASETS.items():
            expected_columns = list(config.get("expected_columns", []))
            if expected_columns and all(col in df.columns for col in expected_columns[:3]):
                return dataset_type

        return "desconhecido"

    def validate_and_clean(self, df: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
        """Apply basic validation/cleaning and add standard metadata fields."""
        df_clean = df.copy()

        # Basic string cleanup
        string_cols = df_clean.select_dtypes(include=["object"]).columns
        for col in string_cols:
            df_clean[col] = (
                df_clean[col]
                .astype(str)
                .str.strip()
            )

        # Dataset-specific checks
        if dataset_type in {"backhaul", "estacoes"}:
            if "latitude" in df_clean.columns and "longitude" in df_clean.columns:
                df_clean["latitude"] = pd.to_numeric(df_clean["latitude"], errors="coerce")
                df_clean["longitude"] = pd.to_numeric(df_clean["longitude"], errors="coerce")
                df_clean = df_clean.dropna(subset=["latitude", "longitude"])

                # Filter roughly to Brazil bounds
                df_clean = df_clean[
                    (df_clean["latitude"].between(-33.75, 5.27))
                    & (df_clean["longitude"].between(-73.99, -34.79))
                ]

            if dataset_type == "backhaul" and "capacidade_mbps" in df_clean.columns:
                df_clean["capacidade_mbps"] = pd.to_numeric(df_clean["capacidade_mbps"], errors="coerce")

            if dataset_type == "estacoes" and "latitude" in df_clean.columns and "longitude" in df_clean.columns:
                df_clean["geohash"] = df_clean.apply(
                    lambda row: self._compute_geohash(row["latitude"], row["longitude"], precision=7),
                    axis=1,
                )

        # Standard metadata (tests assert these exist)
        df_clean["_processamento_data"] = datetime.now().isoformat()
        df_clean["_dataset_tipo"] = dataset_type
        df_clean["_confidence_score"] = 0.9

        return df_clean

    def _compute_geohash(self, lat: float, lon: float, precision: int = 7) -> str:
        if _GEOHASH_AVAILABLE:
            return geohash2.encode(lat, lon, precision)
        return f"{lat:.4f},{lon:.4f}"

    def process_file(self, filepath: Path) -> Dict:
        """Process a single CSV file."""
        filepath = Path(filepath)
        logger.info("Processing: %s", filepath.name)

        try:
            df = None
            for encoding in ("utf-8", "latin-1", "cp1252"):
                try:
                    df = pd.read_csv(filepath, encoding=encoding, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise ValueError(f"Unable to decode {filepath.name} with common encodings")

            dataset_type = self.infer_dataset_type(df, filepath.name)
            df_clean = self.validate_and_clean(df, dataset_type)

            content_hash = hashlib.md5(pd.util.hash_pandas_object(df_clean, index=True).values).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            output_filename = f"anatel_{dataset_type}_{timestamp}_{content_hash}.parquet"
            output_path = self.output_dir / output_filename

            df_clean.to_parquet(output_path, index=False)

            stats = {
                "arquivo_origem": filepath.name,
                "dataset_tipo": dataset_type,
                "registros_processados": int(len(df_clean)),
                "registros_originais": int(len(df)),
                "hash_conteudo": content_hash,
                "caminho_saida": str(output_path),
                "data_processamento": timestamp,
                "colunas": list(df_clean.columns),
            }

            processed_dir = self.manual_dir / "processados"
            processed_dir.mkdir(exist_ok=True)
            shutil.move(str(filepath), str(processed_dir / filepath.name))

            return {"status": "success", "stats": stats}

        except Exception as e:
            logger.exception("Failed to process %s", filepath.name)
            return {"status": "error", "file": filepath.name, "error": str(e)}

    def run(self) -> List[Dict]:
        """Run processing for all new CSV files."""
        files = self.discover_new_files()
        if not files:
            return []

        results: List[Dict] = []
        for filepath in files:
            results.append(self.process_file(filepath))

        self._generate_report(results)
        return results

    def _generate_report(self, results: List[Dict]) -> None:
        report = {
            "data_execucao": datetime.now().isoformat(),
            "total_arquivos": len(results),
            "sucessos": sum(1 for r in results if r.get("status") == "success"),
            "erros": sum(1 for r in results if r.get("status") == "error"),
            "detalhes": results,
        }
        report_path = self.output_dir / f"relatorio_processamento_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def print_instructions() -> None:
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
    print("5. Execute: python -m data_pipeline.connectors.anatel_static_connector")
    print("=" * 60)


# Backwards-compatible alias (existing repo imports/tests used this name)
AnatelStaticConnector = ANATELStaticConnector


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print_instructions()
    connector = ANATELStaticConnector()
    results = connector.run()
    if results:
        success_count = sum(1 for r in results if r.get("status") == "success")
        print(f"\n🎯 Processamento concluído: {success_count}/{len(results)} arquivos processados com sucesso!")
        print("   Os dados estão disponíveis em: data/bronze/anatel/")
    else:
        print("\n⚠️  Nenhum arquivo para processar.")
        print("   Cole os CSVs na pasta 'data/manual/' e execute novamente.")
