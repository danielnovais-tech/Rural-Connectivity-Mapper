"""ML Engine — unified façade for coverage-gap forecasting and prescriptive RL.

Consumes Gold-layer data and produces a combined analysis report that includes:
1. Coverage-gap forecasts (which H3 cells are at risk of degradation)
2. Prescriptive recommendations (optimal infrastructure interventions per cell)

Usage::

    from src.models.ml_engine import MLEngine

    engine = MLEngine()
    report = engine.run(gold_measurements)
    print(report.to_dict())
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.models.coverage_gap_model import (
    CoverageGapForecaster,
    CoverageGapReport,
    snapshots_from_gold,
)
from src.models.prescriptive_rl import (
    PrescriptiveAgent,
    PrescriptiveReport,
    cell_states_from_gold,
)

logger = logging.getLogger(__name__)


@dataclass
class MLEngineReport:
    """Combined ML + RL analysis report."""

    generated_at: str
    data_points_used: int = 0
    h3_cells_analyzed: int = 0
    coverage_gap: CoverageGapReport | None = None
    prescriptive: PrescriptiveReport | None = None

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "data_points_used": self.data_points_used,
            "h3_cells_analyzed": self.h3_cells_analyzed,
            "coverage_gap_forecast": self.coverage_gap.to_dict() if self.coverage_gap else None,
            "prescriptive_recommendations": self.prescriptive.to_dict() if self.prescriptive else None,
        }


class MLEngine:
    """Unified ML + RL engine.

    Parameters
    ----------
    quality_threshold : float
        Quality score below which a cell is considered a coverage gap.
    rl_episodes : int
        Number of RL training episodes.
    gb_estimators : int
        Number of gradient-boosting estimators for the forecaster.
    """

    def __init__(
        self,
        quality_threshold: float = 50.0,
        rl_episodes: int = 500,
        gb_estimators: int = 100,
    ) -> None:
        self._forecaster = CoverageGapForecaster(
            quality_threshold=quality_threshold,
            n_estimators=gb_estimators,
        )
        self._agent = PrescriptiveAgent(episodes=rl_episodes)

    def run(self, gold_measurements: list[dict]) -> MLEngineReport:
        """Run the full ML + RL pipeline on Gold-layer measurements."""
        now = datetime.now(timezone.utc).isoformat()
        report = MLEngineReport(
            generated_at=now,
            data_points_used=len(gold_measurements),
        )

        if not gold_measurements:
            logger.warning("MLEngine.run() called with empty dataset")
            return report

        # ── 1. Coverage-gap forecasting ──────────────────────────────────
        snapshots = snapshots_from_gold(gold_measurements)
        logger.info("Built %d H3 cell snapshots for forecasting", len(snapshots))

        if len(snapshots) >= 5:
            self._forecaster.fit(snapshots)

        gap_report = self._forecaster.predict(snapshots)
        report.coverage_gap = gap_report

        # ── 2. Prescriptive RL ───────────────────────────────────────────
        cell_states = cell_states_from_gold(gold_measurements)
        logger.info("Built %d H3 cell states for RL", len(cell_states))

        if cell_states:
            self._agent.train(cell_states)

        prescriptive_report = self._agent.recommend(cell_states)
        report.prescriptive = prescriptive_report

        report.h3_cells_analyzed = len(snapshots)

        logger.info(
            "MLEngine complete — %d cells, %d at risk, %d recommendations",
            report.h3_cells_analyzed,
            gap_report.cells_at_risk,
            prescriptive_report.cells_with_actions,
        )
        return report
