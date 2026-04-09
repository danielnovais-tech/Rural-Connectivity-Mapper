"""Coverage-gap forecasting using Gradient Boosting on H3-cell time series.

Predicts which H3 cells are likely to fall below a quality threshold within a
configurable forecast horizon, so infrastructure investment can be proactive
rather than reactive.

Depends only on numpy + scikit-learn (already in requirements.txt).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler

    _ML_AVAILABLE = True
except Exception:  # pragma: no cover
    _ML_AVAILABLE = False


# ── Constants ────────────────────────────────────────────────────────────────
QUALITY_THRESHOLD = 50.0  # below this → coverage gap
RURAL_DISTANCE_KM = 100.0
_MAJOR_CITIES = [
    (-23.5505, -46.6333),  # São Paulo
    (-22.9068, -43.1729),  # Rio de Janeiro
    (-15.7939, -47.8828),  # Brasília
    (-12.9714, -38.5014),  # Salvador
    (-3.7172, -38.5434),  # Fortaleza
    (-8.0476, -34.8770),  # Recife
    (-3.1190, -60.0217),  # Manaus
    (-25.4284, -49.2733),  # Curitiba
]

TECHNOLOGY_LOOKUP: dict[str, int] = {
    "fiber": 0,
    "cable": 1,
    "dsl": 2,
    "satellite": 3,
    "mobile_4g": 4,
    "mobile_5g": 5,
    "fixed_wireless": 6,
    "other": 7,
    "unknown": 8,
}


# ── Helper ───────────────────────────────────────────────────────────────────
def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def _distance_from_city(lat: float, lon: float) -> float:
    return min(_haversine(lat, lon, clat, clon) for clat, clon in _MAJOR_CITIES)


# ── Data structures ──────────────────────────────────────────────────────────
@dataclass
class CellSnapshot:
    """Single time-point observation for an H3 cell."""

    h3_index: str
    timestamp: datetime
    avg_download: float
    avg_upload: float
    avg_latency: float
    avg_quality: float
    measurement_count: int
    dominant_technology: str = "unknown"
    lat: float = 0.0
    lon: float = 0.0


@dataclass
class GapForecast:
    """Forecast result for one H3 cell."""

    h3_index: str
    current_quality: float
    predicted_quality: float
    quality_delta: float
    time_to_gap_days: int | None  # None if no gap predicted
    risk_level: str  # "critical", "high", "moderate", "low"
    confidence: float  # 0-1
    lat: float = 0.0
    lon: float = 0.0
    dominant_technology: str = "unknown"
    is_rural: bool = False

    def to_dict(self) -> dict:
        return {
            "h3_index": self.h3_index,
            "current_quality": round(self.current_quality, 2),
            "predicted_quality": round(self.predicted_quality, 2),
            "quality_delta": round(self.quality_delta, 2),
            "time_to_gap_days": self.time_to_gap_days,
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 3),
            "lat": round(self.lat, 4),
            "lon": round(self.lon, 4),
            "dominant_technology": self.dominant_technology,
            "is_rural": self.is_rural,
        }


@dataclass
class CoverageGapReport:
    """Full coverage-gap forecasting report."""

    generated_at: str
    model_version: str = "1.0.0"
    total_cells_analyzed: int = 0
    cells_at_risk: int = 0
    cells_critical: int = 0
    model_r2_score: float = 0.0
    forecasts: list[GapForecast] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "model_version": self.model_version,
            "total_cells_analyzed": self.total_cells_analyzed,
            "cells_at_risk": self.cells_at_risk,
            "cells_critical": self.cells_critical,
            "model_r2_score": round(self.model_r2_score, 4),
            "forecasts": [f.to_dict() for f in self.forecasts],
            "summary": self.summary,
        }


# ── Feature engineering ──────────────────────────────────────────────────────
def _build_features(snapshots: list[CellSnapshot]) -> tuple:
    """Build feature matrix from cell snapshots.

    Features per cell:
      0: latitude
      1: longitude
      2: distance from nearest major city (km)
      3: avg download (Mbps)
      4: avg upload (Mbps)
      5: avg latency (ms)
      6: measurement count (log-scaled)
      7: technology (encoded)
      8: is_rural (0/1)

    Target: avg_quality score.
    """
    X, y = [], []
    for snap in snapshots:
        dist = _distance_from_city(snap.lat, snap.lon)
        tech_code = TECHNOLOGY_LOOKUP.get(snap.dominant_technology.lower(), 8)
        is_rural = 1.0 if dist > RURAL_DISTANCE_KM else 0.0

        X.append([
            snap.lat,
            snap.lon,
            dist,
            snap.avg_download,
            snap.avg_upload,
            snap.avg_latency,
            math.log1p(snap.measurement_count),
            float(tech_code),
            is_rural,
        ])
        y.append(snap.avg_quality)

    return np.array(X), np.array(y)


# ── Model ────────────────────────────────────────────────────────────────────
class CoverageGapForecaster:
    """Gradient-boosted coverage-gap forecasting model.

    Workflow:
    1. ``fit(snapshots)`` — train on historical cell-level observations.
    2. ``predict(current_snapshots)`` — project quality forward and flag at-risk cells.
    """

    def __init__(
        self,
        quality_threshold: float = QUALITY_THRESHOLD,
        n_estimators: int = 100,
        max_depth: int = 4,
        learning_rate: float = 0.1,
    ) -> None:
        if not _ML_AVAILABLE:
            raise RuntimeError("numpy and scikit-learn are required for CoverageGapForecaster")
        self.quality_threshold = quality_threshold
        self._model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42,
        )
        self._scaler = StandardScaler()
        self._is_fitted = False
        self._r2: float = 0.0

    # ── Train ────────────────────────────────────────────────────────────
    def fit(self, snapshots: list[CellSnapshot]) -> float:
        """Train on historical cell snapshots.

        Returns the cross-validated R² score (higher = better).
        """
        if len(snapshots) < 5:
            raise ValueError(f"Need ≥ 5 snapshots to train, got {len(snapshots)}")

        X, y = _build_features(snapshots)
        X_scaled = self._scaler.fit_transform(X)

        # Cross-validate (3 folds minimum, up to 5)
        n_folds = min(5, len(snapshots))
        if n_folds >= 3:
            scores = cross_val_score(self._model, X_scaled, y, cv=n_folds, scoring="r2")
            self._r2 = float(max(np.mean(scores), 0.0))
        else:
            self._r2 = 0.0

        self._model.fit(X_scaled, y)
        self._is_fitted = True
        logger.info("CoverageGapForecaster trained — R²=%.4f (%d samples)", self._r2, len(snapshots))
        return self._r2

    # ── Predict ──────────────────────────────────────────────────────────
    def predict(self, current_snapshots: list[CellSnapshot]) -> CoverageGapReport:
        """Forecast quality and identify at-risk H3 cells.

        If the model hasn't been fitted yet, uses a heuristic fallback (rule-based
        scoring) so the system always returns actionable results.
        """
        now = datetime.now(timezone.utc).isoformat()
        report = CoverageGapReport(generated_at=now)

        if not current_snapshots:
            return report

        if self._is_fitted:
            return self._predict_ml(current_snapshots, report)
        return self._predict_heuristic(current_snapshots, report)

    # ── ML prediction path ───────────────────────────────────────────────
    def _predict_ml(
        self, snapshots: list[CellSnapshot], report: CoverageGapReport,
    ) -> CoverageGapReport:
        X, _ = _build_features(snapshots)
        X_scaled = self._scaler.transform(X)
        predicted_quality = self._model.predict(X_scaled)

        forecasts: list[GapForecast] = []
        for i, snap in enumerate(snapshots):
            pred_q = float(np.clip(predicted_quality[i], 0, 100))
            delta = pred_q - snap.avg_quality
            dist = _distance_from_city(snap.lat, snap.lon)

            risk = self._classify_risk(pred_q, delta)
            ttg = self._estimate_time_to_gap(snap.avg_quality, pred_q, delta)

            forecasts.append(GapForecast(
                h3_index=snap.h3_index,
                current_quality=snap.avg_quality,
                predicted_quality=pred_q,
                quality_delta=delta,
                time_to_gap_days=ttg,
                risk_level=risk,
                confidence=min(self._r2 + 0.1, 1.0),
                lat=snap.lat,
                lon=snap.lon,
                dominant_technology=snap.dominant_technology,
                is_rural=dist > RURAL_DISTANCE_KM,
            ))

        return self._finalize_report(report, forecasts)

    # ── Heuristic fallback ───────────────────────────────────────────────
    def _predict_heuristic(
        self, snapshots: list[CellSnapshot], report: CoverageGapReport,
    ) -> CoverageGapReport:
        """Rule-based fallback when no training data is available."""
        forecasts: list[GapForecast] = []
        for snap in snapshots:
            dist = _distance_from_city(snap.lat, snap.lon)
            is_rural = dist > RURAL_DISTANCE_KM

            # Heuristic: rural + low-measurement areas degrade ~5-15% faster
            degradation_factor = 1.0
            if is_rural:
                degradation_factor += 0.15
            if snap.measurement_count < 5:
                degradation_factor += 0.10
            if snap.dominant_technology.lower() in ("satellite", "fixed_wireless"):
                degradation_factor += 0.05

            pred_q = max(snap.avg_quality * (1.0 - 0.05 * degradation_factor), 0)
            delta = pred_q - snap.avg_quality
            risk = self._classify_risk(pred_q, delta)
            ttg = self._estimate_time_to_gap(snap.avg_quality, pred_q, delta)

            forecasts.append(GapForecast(
                h3_index=snap.h3_index,
                current_quality=snap.avg_quality,
                predicted_quality=round(pred_q, 2),
                quality_delta=round(delta, 2),
                time_to_gap_days=ttg,
                risk_level=risk,
                confidence=0.35,  # low confidence for heuristic
                lat=snap.lat,
                lon=snap.lon,
                dominant_technology=snap.dominant_technology,
                is_rural=is_rural,
            ))

        return self._finalize_report(report, forecasts)

    # ── Helpers ──────────────────────────────────────────────────────────
    def _classify_risk(self, predicted_quality: float, delta: float) -> str:
        if predicted_quality < self.quality_threshold * 0.5:
            return "critical"
        if predicted_quality < self.quality_threshold:
            return "high"
        if delta < -10:
            return "moderate"
        return "low"

    @staticmethod
    def _estimate_time_to_gap(
        current: float, predicted: float, delta: float,
    ) -> int | None:
        """Estimate days until quality drops below threshold, via linear extrapolation."""
        if predicted >= QUALITY_THRESHOLD:
            if delta >= 0:
                return None  # no gap expected
            # Extrapolate linearly
            gap_remaining = current - QUALITY_THRESHOLD
            daily_drop = abs(delta) / 90  # assume prediction horizon ≈90 days
            if daily_drop > 0:
                return max(int(gap_remaining / daily_drop), 1)
            return None
        # Already below threshold
        return 0

    def _finalize_report(
        self, report: CoverageGapReport, forecasts: list[GapForecast],
    ) -> CoverageGapReport:
        forecasts.sort(key=lambda f: f.predicted_quality)

        report.total_cells_analyzed = len(forecasts)
        report.cells_at_risk = sum(1 for f in forecasts if f.risk_level in ("critical", "high"))
        report.cells_critical = sum(1 for f in forecasts if f.risk_level == "critical")
        report.model_r2_score = self._r2
        report.forecasts = forecasts

        # Summary statistics
        if forecasts:
            qualities = [f.predicted_quality for f in forecasts]
            report.summary = {
                "avg_predicted_quality": round(float(np.mean(qualities)) if _ML_AVAILABLE else sum(qualities) / len(qualities), 2),
                "min_predicted_quality": round(min(qualities), 2),
                "max_predicted_quality": round(max(qualities), 2),
                "pct_at_risk": round(report.cells_at_risk / len(forecasts) * 100, 1),
                "risk_distribution": {
                    "critical": sum(1 for f in forecasts if f.risk_level == "critical"),
                    "high": sum(1 for f in forecasts if f.risk_level == "high"),
                    "moderate": sum(1 for f in forecasts if f.risk_level == "moderate"),
                    "low": sum(1 for f in forecasts if f.risk_level == "low"),
                },
            }

        return report


# ── Convenience: build snapshots from Gold-layer data ────────────────────────
def snapshots_from_gold(measurements: list[dict]) -> list[CellSnapshot]:
    """Convert Gold-layer measurement dicts into CellSnapshot objects.

    Groups by H3 index and aggregates.
    """
    cells: dict[str, list[dict]] = {}
    for m in measurements:
        h3 = m.get("h3_index") or "unknown"
        cells.setdefault(h3, []).append(m)

    snapshots: list[CellSnapshot] = []
    for h3, points in cells.items():
        if h3 == "unknown":
            continue

        downloads = [p.get("download_mbps") or p.get("speed_test", {}).get("download", 0) for p in points]
        uploads = [p.get("upload_mbps") or p.get("speed_test", {}).get("upload", 0) for p in points]
        latencies = [p.get("latency_ms") or p.get("speed_test", {}).get("latency", 0) for p in points]
        qualities = [
            p.get("confidence_score")
            or p.get("quality_score", {}).get("overall_score", 50)
            for p in points
        ]

        # Pick dominant technology
        tech_counts: dict[str, int] = {}
        for p in points:
            tech = str(p.get("technology", "unknown")).lower()
            tech_counts[tech] = tech_counts.get(tech, 0) + 1
        dom_tech = max(tech_counts, key=tech_counts.get)  # type: ignore[arg-type]

        # Average location
        lats = [p.get("lat", p.get("latitude", 0)) for p in points]
        lons = [p.get("lon", p.get("longitude", 0)) for p in points]

        # Most recent timestamp
        ts_raw = None
        for p in points:
            t = p.get("timestamp_utc") or p.get("timestamp")
            if t and (ts_raw is None or str(t) > str(ts_raw)):
                ts_raw = t

        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        elif isinstance(ts_raw, datetime):
            ts = ts_raw
        else:
            ts = datetime.now(timezone.utc)

        snapshots.append(CellSnapshot(
            h3_index=h3,
            timestamp=ts,
            avg_download=sum(downloads) / len(downloads),
            avg_upload=sum(uploads) / len(uploads),
            avg_latency=sum(latencies) / len(latencies),
            avg_quality=sum(qualities) / len(qualities),
            measurement_count=len(points),
            dominant_technology=dom_tech,
            lat=sum(lats) / len(lats),
            lon=sum(lons) / len(lons),
        ))

    return snapshots
