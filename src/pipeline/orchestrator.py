"""Pipeline orchestrator for end-to-end data processing."""

from pathlib import Path

from src.sources import DataSource

from .bronze import BronzeLayer
from .gold import GoldLayer
from .silver import SilverLayer


class PipelineOrchestrator:
    """Orchestrates the end-to-end data pipeline (bronze → silver → gold).

    Manages the flow of data through all layers and provides a simple
    interface for running the complete pipeline.
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        bronze_dir: Path | None = None,
        silver_dir: Path | None = None,
        gold_dir: Path | None = None,
    ):
        """Initialize pipeline orchestrator.

        Args:
            data_dir: Base data directory (default: ./data)
            bronze_dir: Bronze layer directory (overrides data_dir/bronze)
            silver_dir: Silver layer directory (overrides data_dir/silver)
            gold_dir: Gold layer directory (overrides data_dir/gold)
        """
        # Set up directories
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"

        data_dir = Path(data_dir)

        self.bronze_dir = Path(bronze_dir) if bronze_dir else data_dir / "bronze"
        self.silver_dir = Path(silver_dir) if silver_dir else data_dir / "silver"
        self.gold_dir = Path(gold_dir) if gold_dir else data_dir / "gold"

        # Initialize layers
        self.bronze = BronzeLayer(self.bronze_dir)
        self.silver = SilverLayer(self.silver_dir)
        self.gold = GoldLayer(self.gold_dir)

    def run(self, sources: list[DataSource]) -> None:
        """Run the complete pipeline with the given sources.

        Args:
            sources: List of DataSource instances to ingest
        """
        print("=" * 70)
        print("🚀 STARTING DATA PIPELINE")
        print("=" * 70)

        # Step 1: Ingest to Bronze
        print("\n📥 BRONZE LAYER: Ingesting raw data...")
        for source in sources:
            self.bronze.ingest(source)

        # Step 2: Process to Silver
        bronze_measurements = self.bronze.read_all()
        silver_measurements = self.silver.process(bronze_measurements)

        # Step 3: Aggregate to Gold
        gold_files = self.gold.process(silver_measurements)

        # Summary
        print("\n" + "=" * 70)
        print("✅ PIPELINE COMPLETE")
        print("=" * 70)
        print("\n📊 Summary:")
        print(f"  Bronze (raw):        {len(bronze_measurements)} measurements")
        print(f"  Silver (processed):  {len(silver_measurements)} measurements")
        print(f"  Gold (aggregated):   {len(gold_files)} files created")
        print("\n📁 Output directories:")
        print(f"  Bronze: {self.bronze_dir}")
        print(f"  Silver: {self.silver_dir}")
        print(f"  Gold:   {self.gold_dir}")
        print()
