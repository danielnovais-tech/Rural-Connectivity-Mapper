"""Tests for ML coverage-gap forecasting and RL prescriptive recommendations."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_measurement(
    lat: float,
    lon: float,
    download: float,
    upload: float,
    latency: float,
    quality: float,
    h3_index: str,
    technology: str = "satellite",
    provider: str = "Starlink",
) -> dict:
    """Create a Gold-layer-style measurement dict."""
    return {
        "id": f"m-{lat}-{lon}",
        "lat": lat,
        "lon": lon,
        "latitude": lat,
        "longitude": lon,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "download_mbps": download,
        "upload_mbps": upload,
        "latency_ms": latency,
        "confidence_score": quality,
        "quality_score": {"overall_score": quality, "rating": "Fair"},
        "h3_index": h3_index,
        "technology": technology,
        "provider": provider,
        "speed_test": {
            "download": download,
            "upload": upload,
            "latency": latency,
        },
    }


def _sample_measurements(n: int = 20) -> list[dict]:
    """Generate diverse sample measurements across Brazil."""
    points = [
        # Rural Amazon — poor quality
        (-3.12, -60.02, 5, 1, 120, 25, "870000000000000", "satellite"),
        (-2.50, -59.50, 8, 2, 100, 30, "870000000000001", "satellite"),
        # Rural Nordeste — poor quality
        (-8.05, -34.88, 12, 3, 80, 35, "870000000000002", "mobile_4g"),
        (-9.67, -35.74, 10, 2, 90, 32, "870000000000003", "mobile_4g"),
        # Semi-rural Centro-Oeste — fair quality
        (-15.78, -47.93, 25, 8, 50, 55, "870000000000004", "fixed_wireless"),
        (-14.23, -51.92, 30, 10, 45, 60, "870000000000005", "fiber"),
        # Urban São Paulo — good quality
        (-23.55, -46.63, 100, 40, 15, 85, "870000000000006", "fiber"),
        (-23.56, -46.64, 120, 50, 12, 90, "870000000000007", "fiber"),
        # Urban Rio — good quality
        (-22.91, -43.17, 80, 30, 20, 78, "870000000000008", "cable"),
        (-22.92, -43.18, 90, 35, 18, 82, "870000000000009", "cable"),
        # Rural Sul — moderate quality
        (-25.43, -49.27, 40, 15, 35, 65, "87000000000000a", "mobile_4g"),
        (-26.30, -48.85, 35, 12, 40, 58, "87000000000000b", "mobile_4g"),
        # Very remote — critical
        (-1.00, -62.00, 2, 0.5, 200, 15, "87000000000000c", "satellite"),
        (-4.00, -63.00, 3, 0.8, 180, 18, "87000000000000d", "satellite"),
        # Medium quality various
        (-12.97, -38.50, 45, 15, 30, 70, "87000000000000e", "fiber"),
        (-10.50, -37.00, 20, 6, 60, 45, "87000000000000f", "fixed_wireless"),
        (-7.12, -34.86, 55, 20, 25, 72, "870000000000010", "cable"),
        (-16.68, -49.25, 30, 10, 55, 50, "870000000000011", "mobile_4g"),
        (-5.80, -35.21, 15, 4, 70, 40, "870000000000012", "fixed_wireless"),
        (-19.92, -43.94, 65, 25, 22, 75, "870000000000013", "fiber"),
    ]

    measurements = []
    for p in points[:n]:
        measurements.append(_make_measurement(*p))
    return measurements


# ══════════════════════════════════════════════════════════════════════════════
# Coverage-Gap Forecasting Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestCoverageGapModel:
    """Tests for CoverageGapForecaster."""

    def test_snapshots_from_gold(self):
        from src.models.coverage_gap_model import snapshots_from_gold

        data = _sample_measurements(10)
        snapshots = snapshots_from_gold(data)
        assert len(snapshots) == 10  # each has unique H3
        assert all(s.h3_index != "unknown" for s in snapshots)
        assert all(s.avg_download > 0 for s in snapshots)

    def test_snapshots_skip_unknown_h3(self):
        from src.models.coverage_gap_model import snapshots_from_gold

        data = [_make_measurement(-10, -50, 20, 5, 40, 50, "unknown")]
        snapshots = snapshots_from_gold(data)
        assert len(snapshots) == 0

    def test_snapshots_aggregate_same_h3(self):
        from src.models.coverage_gap_model import snapshots_from_gold

        data = [
            _make_measurement(-10, -50, 20, 5, 40, 50, "870000000000099"),
            _make_measurement(-10.01, -50.01, 40, 10, 30, 70, "870000000000099"),
        ]
        snapshots = snapshots_from_gold(data)
        assert len(snapshots) == 1
        assert snapshots[0].avg_download == pytest.approx(30.0)
        assert snapshots[0].avg_quality == pytest.approx(60.0)
        assert snapshots[0].measurement_count == 2

    def test_forecaster_heuristic_fallback(self):
        """Without training, the forecaster uses a heuristic fallback."""
        from src.models.coverage_gap_model import CoverageGapForecaster, snapshots_from_gold

        data = _sample_measurements(3)  # too few to train
        snapshots = snapshots_from_gold(data)
        forecaster = CoverageGapForecaster()
        report = forecaster.predict(snapshots)

        assert report.total_cells_analyzed == len(snapshots)
        assert len(report.forecasts) == len(snapshots)
        for f in report.forecasts:
            assert f.confidence == pytest.approx(0.35)  # heuristic confidence
            assert f.risk_level in ("critical", "high", "moderate", "low")

    def test_forecaster_fit_and_predict(self):
        """Train on 20 samples and verify ML prediction path."""
        from src.models.coverage_gap_model import CoverageGapForecaster, snapshots_from_gold

        data = _sample_measurements(20)
        snapshots = snapshots_from_gold(data)
        forecaster = CoverageGapForecaster()

        r2 = forecaster.fit(snapshots)
        assert isinstance(r2, float)
        assert r2 >= 0.0  # R² can't be negative (we clamp)

        report = forecaster.predict(snapshots)
        assert report.total_cells_analyzed == 20
        assert report.model_r2_score >= 0.0
        assert all(0 <= f.predicted_quality <= 100 for f in report.forecasts)
        assert all(f.h3_index for f in report.forecasts)

    def test_forecaster_identifies_critical_cells(self):
        from src.models.coverage_gap_model import CoverageGapForecaster, snapshots_from_gold

        data = _sample_measurements(20)
        snapshots = snapshots_from_gold(data)
        forecaster = CoverageGapForecaster()
        forecaster.fit(snapshots)
        report = forecaster.predict(snapshots)

        # We have cells with quality 15-25, should be flagged as critical or high
        risk_levels = {f.risk_level for f in report.forecasts}
        assert "critical" in risk_levels or "high" in risk_levels

    def test_forecaster_report_serialisation(self):
        from src.models.coverage_gap_model import CoverageGapForecaster, snapshots_from_gold

        data = _sample_measurements(10)
        snapshots = snapshots_from_gold(data)
        forecaster = CoverageGapForecaster()
        forecaster.fit(snapshots)
        report = forecaster.predict(snapshots)

        d = report.to_dict()
        assert "generated_at" in d
        assert "forecasts" in d
        assert isinstance(d["forecasts"], list)
        assert "summary" in d

    def test_forecaster_empty_input(self):
        from src.models.coverage_gap_model import CoverageGapForecaster

        forecaster = CoverageGapForecaster()
        report = forecaster.predict([])
        assert report.total_cells_analyzed == 0
        assert report.forecasts == []

    def test_forecaster_fit_too_few_raises(self):
        from src.models.coverage_gap_model import CoverageGapForecaster, CellSnapshot

        forecaster = CoverageGapForecaster()
        with pytest.raises(ValueError, match="≥ 5"):
            forecaster.fit([
                CellSnapshot("h3_1", datetime.now(timezone.utc), 10, 5, 50, 40, 3)
            ])

    def test_risk_classification(self):
        from src.models.coverage_gap_model import CoverageGapForecaster

        f = CoverageGapForecaster(quality_threshold=50.0)
        assert f._classify_risk(20, -5) == "critical"   # <50*0.5=25
        assert f._classify_risk(40, -5) == "high"       # <50
        assert f._classify_risk(60, -15) == "moderate"   # >=50 but delta < -10
        assert f._classify_risk(70, -5) == "low"


# ══════════════════════════════════════════════════════════════════════════════
# Prescriptive RL Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestPrescriptiveRL:
    """Tests for PrescriptiveAgent (Q-learning)."""

    def test_cell_states_from_gold(self):
        from src.models.prescriptive_rl import cell_states_from_gold

        data = _sample_measurements(10)
        states = cell_states_from_gold(data)
        assert len(states) == 10
        assert all(s.h3_index for s in states)
        assert any(s.is_rural for s in states)
        assert any(not s.is_rural for s in states)

    def test_state_key_format(self):
        from src.models.prescriptive_rl import CellState

        cell = CellState(
            h3_index="abc", quality_score=30, technology="satellite",
            is_rural=True,
        )
        key = cell.state_key
        assert key == "poor|satellite_wireless|rural"

    def test_agent_greedy_fallback(self):
        """Without training, the agent uses reward-greedy fallback."""
        from src.models.prescriptive_rl import PrescriptiveAgent, cell_states_from_gold

        data = _sample_measurements(5)
        states = cell_states_from_gold(data)
        agent = PrescriptiveAgent()
        report = agent.recommend(states)

        assert report.total_cells == 5
        assert len(report.recommendations) > 0
        # All recs should have valid actions
        from src.models.prescriptive_rl import Action
        valid_actions = {a.value for a in Action}
        for rec in report.recommendations:
            assert rec.action in valid_actions

    def test_agent_train_and_recommend(self):
        from src.models.prescriptive_rl import PrescriptiveAgent, cell_states_from_gold

        data = _sample_measurements(20)
        states = cell_states_from_gold(data)
        agent = PrescriptiveAgent(episodes=100)  # fewer for speed

        episodes = agent.train(states)
        assert episodes == 100

        report = agent.recommend(states)
        assert report.total_episodes_trained == 100
        assert report.cells_with_actions > 0
        # Recommendations should be ranked
        ranks = [r.priority_rank for r in report.recommendations]
        assert ranks == sorted(ranks)

    def test_agent_rural_priority(self):
        """Rural cells with poor quality should get higher ROI scores."""
        from src.models.prescriptive_rl import PrescriptiveAgent, CellState

        urban_good = CellState("u1", quality_score=80, technology="fiber", is_rural=False)
        rural_poor = CellState("r1", quality_score=25, technology="satellite", is_rural=True)

        agent = PrescriptiveAgent(episodes=200)
        agent.train([urban_good, rural_poor])
        report = agent.recommend([urban_good, rural_poor])

        # Rural poor cell should have an action recommendation
        rural_recs = [r for r in report.recommendations if r.h3_index == "r1"]
        assert len(rural_recs) == 1
        assert rural_recs[0].roi_score > 0

    def test_reward_function(self):
        from src.models.prescriptive_rl import PrescriptiveAgent, CellState, Action

        cell = CellState("h3", quality_score=30, technology="satellite", is_rural=True)
        reward, uplift, cost = PrescriptiveAgent._reward(cell, Action.DEPLOY_SATELLITE)

        assert reward > 0
        assert uplift > 0
        assert cost == pytest.approx(0.35)

    def test_action_params_all_have_required_keys(self):
        from src.models.prescriptive_rl import ACTION_PARAMS, Action

        required = {"cost", "quality_uplift", "best_for", "min_quality_unlock",
                     "description_en", "description_pt"}
        for action in Action:
            assert action in ACTION_PARAMS, f"Missing params for {action}"
            assert required.issubset(ACTION_PARAMS[action].keys())

    def test_report_serialisation(self):
        from src.models.prescriptive_rl import PrescriptiveAgent, cell_states_from_gold

        data = _sample_measurements(5)
        states = cell_states_from_gold(data)
        agent = PrescriptiveAgent(episodes=50)
        agent.train(states)
        report = agent.recommend(states)

        d = report.to_dict()
        assert "recommendations" in d
        assert isinstance(d["recommendations"], list)
        assert "policy_summary" in d

    def test_empty_input(self):
        from src.models.prescriptive_rl import PrescriptiveAgent

        agent = PrescriptiveAgent()
        episodes = agent.train([])
        assert episodes == 0
        report = agent.recommend([])
        assert report.total_cells == 0
        assert report.recommendations == []

    def test_quality_bucket_boundaries(self):
        from src.models.prescriptive_rl import _quality_bucket

        assert _quality_bucket(0) == "critical"
        assert _quality_bucket(24.9) == "critical"
        assert _quality_bucket(25) == "poor"
        assert _quality_bucket(39.9) == "poor"
        assert _quality_bucket(40) == "fair"
        assert _quality_bucket(59.9) == "fair"
        assert _quality_bucket(60) == "good"
        assert _quality_bucket(79.9) == "good"
        assert _quality_bucket(80) == "excellent"
        assert _quality_bucket(100) == "excellent"

    def test_tech_group_mapping(self):
        from src.models.prescriptive_rl import _tech_group

        assert _tech_group("fiber") == "fiber_cable"
        assert _tech_group("cable") == "fiber_cable"
        assert _tech_group("dsl") == "fiber_cable"
        assert _tech_group("mobile_4g") == "mobile"
        assert _tech_group("mobile_5g") == "mobile"
        assert _tech_group("satellite") == "satellite_wireless"
        assert _tech_group("fixed_wireless") == "satellite_wireless"
        assert _tech_group("unknown") == "other"


# ══════════════════════════════════════════════════════════════════════════════
# ML Engine Integration Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestMLEngine:
    """Tests for the unified MLEngine orchestrator."""

    def test_full_run(self):
        from src.models.ml_engine import MLEngine

        data = _sample_measurements(20)
        engine = MLEngine(rl_episodes=100, gb_estimators=50)
        report = engine.run(data)

        assert report.data_points_used == 20
        assert report.h3_cells_analyzed == 20
        assert report.coverage_gap is not None
        assert report.prescriptive is not None
        assert report.coverage_gap.total_cells_analyzed == 20
        assert report.prescriptive.total_cells > 0

    def test_full_run_small_dataset(self):
        """Under 5 snapshots: forecaster uses heuristic, RL still works."""
        from src.models.ml_engine import MLEngine

        data = _sample_measurements(3)
        engine = MLEngine(rl_episodes=50)
        report = engine.run(data)

        assert report.coverage_gap is not None
        assert report.prescriptive is not None
        # Heuristic — all forecasts have low confidence
        for f in report.coverage_gap.forecasts:
            assert f.confidence == pytest.approx(0.35)

    def test_empty_run(self):
        from src.models.ml_engine import MLEngine

        engine = MLEngine()
        report = engine.run([])
        assert report.data_points_used == 0
        assert report.coverage_gap is None
        assert report.prescriptive is None

    def test_report_to_dict(self):
        from src.models.ml_engine import MLEngine

        data = _sample_measurements(10)
        engine = MLEngine(rl_episodes=50, gb_estimators=30)
        report = engine.run(data)
        d = report.to_dict()

        assert "coverage_gap_forecast" in d
        assert "prescriptive_recommendations" in d
        assert d["data_points_used"] == 10

    def test_combined_insights(self):
        """At-risk cells from forecaster should have recommendations from RL."""
        from src.models.ml_engine import MLEngine

        data = _sample_measurements(20)
        engine = MLEngine(rl_episodes=200, gb_estimators=50)
        report = engine.run(data)

        at_risk_h3 = {
            f.h3_index
            for f in report.coverage_gap.forecasts
            if f.risk_level in ("critical", "high")
        }
        recommended_h3 = {r.h3_index for r in report.prescriptive.recommendations}

        # At-risk cells should generally have recommendations
        if at_risk_h3:
            overlap = at_risk_h3 & recommended_h3
            assert len(overlap) > 0, "Expected at-risk cells to have recommendations"
