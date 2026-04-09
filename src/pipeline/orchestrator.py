"""Pipeline orchestrator for end-to-end data processing."""

from pathlib import Path

from src.sources import DataSource

from .audit import AuditEntry, PipelineAuditLog
from .bronze import BronzeLayer
from .fusion_engine import FusionEngine
from .gold import GoldLayer
from .silver import SilverLayer


class PipelineOrchestrator:
    """Orchestrates the end-to-end data pipeline (bronze → fusion → silver → gold).

    Manages the flow of data through all layers and provides a simple
    interface for running the complete pipeline.

    Supports two execution modes:
    - ``production``: only real (non-synthetic) data sources are processed.
    - ``demo``: all sources are processed including mock/synthetic ones.
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        bronze_dir: Path | None = None,
        silver_dir: Path | None = None,
        gold_dir: Path | None = None,
        use_fusion: bool = True,
        mode: str = "demo",
    ):
        """Initialize pipeline orchestrator.

        Args:
            data_dir: Base data directory (default: ./data)
            bronze_dir: Bronze layer directory (overrides data_dir/bronze)
            silver_dir: Silver layer directory (overrides data_dir/silver)
            gold_dir: Gold layer directory (overrides data_dir/gold)
            use_fusion: Whether to use fusion engine (default: True)
            mode: ``"production"`` excludes synthetic sources; ``"demo"`` includes them.
        """
        # Set up directories
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"

        data_dir = Path(data_dir)

        self.bronze_dir = Path(bronze_dir) if bronze_dir else data_dir / "bronze"
        self.silver_dir = Path(silver_dir) if silver_dir else data_dir / "silver"
        self.gold_dir = Path(gold_dir) if gold_dir else data_dir / "gold"
        self.use_fusion = use_fusion
        self.mode = mode

        # Initialize layers
        self.bronze = BronzeLayer(self.bronze_dir)
        self.fusion = FusionEngine(self.bronze_dir, self.silver_dir)
        self.silver = SilverLayer(self.silver_dir)
        self.gold = GoldLayer(self.gold_dir)
        self.audit = PipelineAuditLog(data_dir / "audit")

    def run(self, sources: list[DataSource]) -> None:
        """Run the complete pipeline with the given sources.

        In production mode, synthetic sources are automatically excluded.

        Args:
            sources: List of DataSource instances to ingest
        """
        # Filter sources based on mode
        if self.mode == "production":
            active_sources = [s for s in sources if not s.is_synthetic]
            skipped = [s for s in sources if s.is_synthetic]
            if skipped:
                names = ", ".join(s.source_name for s in skipped)
                print(f"⚠  Production mode: skipping synthetic sources → {names}")
        else:
            active_sources = list(sources)

        # Start audit entry
        source_info = [
            {"name": s.source_name, "class": s.__class__.__name__, "synthetic": s.is_synthetic}
            for s in active_sources
        ]
        entry: AuditEntry = self.audit.start_run(mode=self.mode, sources=source_info)

        print("=" * 70)
        print(f"🚀 STARTING DATA PIPELINE  [mode={self.mode}, run_id={entry.run_id[:12]}…]")
        print("=" * 70)

        try:
            # Step 1: Ingest to Bronze
            print("\n📥 BRONZE LAYER: Ingesting raw data...")
            for source in active_sources:
                self.bronze.ingest(source)

            # Step 2: Fusion (optional, unify sources and calculate ICR)
            if self.use_fusion:
                fused_measurements = self.fusion.process()
                bronze_measurements = fused_measurements
            else:
                bronze_measurements = self.bronze.read_all()

            synthetic_count = sum(
                1 for m in bronze_measurements if getattr(m, "lineage", None) and m.lineage.is_synthetic
            )
            entry.record_bronze(len(bronze_measurements), synthetic=synthetic_count)

            # Step 3: Process to Silver
            silver_measurements = self.silver.process(bronze_measurements)
            entry.record_silver(len(silver_measurements))

            # Step 4: Aggregate to Gold
            gold_files = self.gold.process(silver_measurements)
            entry.record_gold(gold_files)

        except Exception as exc:
            entry.add_error(str(exc))
            self.audit.commit(entry)
            raise

        # Commit audit entry
        self.audit.commit(entry)

        # Summary
        print("\n" + "=" * 70)
        print("✅ PIPELINE COMPLETE")
        print("=" * 70)
        print(f"\n📊 Summary  (run {entry.run_id[:12]}…):")
        print(f"  Mode:                {self.mode}")
        print(f"  Bronze (raw):        {len(bronze_measurements)} measurements ({synthetic_count} synthetic, {len(bronze_measurements) - synthetic_count} real)")
        print(f"  Silver (processed):  {len(silver_measurements)} measurements")
        print(f"  Gold (aggregated):   {len(gold_files)} files created")
        if self.use_fusion:
            print("  Fusion: ✓ Enabled (ICR calculated)")
        print(f"\n📁 Output directories:")
        print(f"  Bronze: {self.bronze_dir}")
        print(f"  Silver: {self.silver_dir}")
        print(f"  Gold:   {self.gold_dir}")
        print(f"  Audit:  {self.audit.audit_dir}")
        print()
