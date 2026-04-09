"""Prescriptive-recommendation engine using tabular Q-learning.

Given the current connectivity state of H3 cells, the agent learns an optimal
*intervention policy* — which infrastructure action maximises long-term quality
improvement per unit of estimated cost.

Design choices:
* **Tabular Q-learning** — lightweight, interpretable, no GPU / PyTorch needed.
* **State** discretised by (quality_bucket, technology, rurality) → small table.
* **Actions** = realistic ISP / government interventions.
* **Reward** = quality_improvement × rural_multiplier / normalised_cost.

Depends only on numpy (already in requirements.txt).
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import numpy as np

    _NP = True
except Exception:  # pragma: no cover
    np = None  # type: ignore[assignment]
    _NP = False


# ── Action space ─────────────────────────────────────────────────────────────

class Action(str, Enum):
    DEPLOY_SATELLITE = "deploy_satellite"
    UPGRADE_FIBER = "upgrade_fiber"
    ADD_4G_TOWER = "add_4g_tower"
    ADD_5G_SMALL_CELL = "add_5g_small_cell"
    ADD_FIXED_WIRELESS = "add_fixed_wireless"
    COMMUNITY_WIFI = "community_wifi"
    MAINTAIN = "maintain"


# Estimated cost (normalised 0-1) and expected quality uplift per action.
# Real values should be calibrated from field data; these are reasonable
# defaults for Brazil's rural connectivity programmes.
ACTION_PARAMS: dict[str, dict] = {
    Action.DEPLOY_SATELLITE: {
        "cost": 0.35,
        "quality_uplift": 25.0,
        "best_for": ["satellite", "unknown", "other"],
        "min_quality_unlock": 0,  # works anywhere
        "description_en": "Deploy satellite terminal (e.g. Starlink)",
        "description_pt": "Instalar terminal satelital (ex: Starlink)",
    },
    Action.UPGRADE_FIBER: {
        "cost": 0.90,
        "quality_uplift": 45.0,
        "best_for": ["fiber", "cable", "dsl"],
        "min_quality_unlock": 20,
        "description_en": "Extend fiber-optic backbone to the area",
        "description_pt": "Estender backbone de fibra óptica à região",
    },
    Action.ADD_4G_TOWER: {
        "cost": 0.60,
        "quality_uplift": 30.0,
        "best_for": ["mobile_4g", "mobile_5g"],
        "min_quality_unlock": 10,
        "description_en": "Install 4G macro cell tower",
        "description_pt": "Instalar torre macro 4G",
    },
    Action.ADD_5G_SMALL_CELL: {
        "cost": 0.50,
        "quality_uplift": 40.0,
        "best_for": ["mobile_5g"],
        "min_quality_unlock": 40,
        "description_en": "Install 5G small cell",
        "description_pt": "Instalar small cell 5G",
    },
    Action.ADD_FIXED_WIRELESS: {
        "cost": 0.40,
        "quality_uplift": 20.0,
        "best_for": ["fixed_wireless", "satellite"],
        "min_quality_unlock": 0,
        "description_en": "Deploy fixed-wireless access point",
        "description_pt": "Instalar ponto de acesso fixo sem fio",
    },
    Action.COMMUNITY_WIFI: {
        "cost": 0.15,
        "quality_uplift": 12.0,
        "best_for": ["other", "unknown"],
        "min_quality_unlock": 0,
        "description_en": "Set up community WiFi hotspot",
        "description_pt": "Configurar ponto WiFi comunitário",
    },
    Action.MAINTAIN: {
        "cost": 0.05,
        "quality_uplift": 2.0,
        "best_for": [],
        "min_quality_unlock": 0,
        "description_en": "Maintain current infrastructure",
        "description_pt": "Manter infraestrutura atual",
    },
}


# ── State discretisation ─────────────────────────────────────────────────────

QUALITY_BUCKETS = ["critical", "poor", "fair", "good", "excellent"]
TECH_GROUPS = ["fiber_cable", "mobile", "satellite_wireless", "other"]
RURALITY = ["urban", "rural"]


def _quality_bucket(score: float) -> str:
    if score < 25:
        return "critical"
    if score < 40:
        return "poor"
    if score < 60:
        return "fair"
    if score < 80:
        return "good"
    return "excellent"


def _tech_group(tech: str) -> str:
    t = tech.lower()
    if t in ("fiber", "cable", "dsl"):
        return "fiber_cable"
    if t in ("mobile_4g", "mobile_5g"):
        return "mobile"
    if t in ("satellite", "fixed_wireless"):
        return "satellite_wireless"
    return "other"


def _rurality(is_rural: bool) -> str:
    return "rural" if is_rural else "urban"


def _state_key(quality_bucket: str, tech_group: str, rurality: str) -> str:
    return f"{quality_bucket}|{tech_group}|{rurality}"


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class CellState:
    """Discretised state of an H3 cell for the RL agent."""

    h3_index: str
    quality_score: float
    technology: str
    is_rural: bool
    lat: float = 0.0
    lon: float = 0.0
    measurement_count: int = 0
    download_mbps: float = 0.0
    upload_mbps: float = 0.0
    latency_ms: float = 0.0

    @property
    def state_key(self) -> str:
        return _state_key(
            _quality_bucket(self.quality_score),
            _tech_group(self.technology),
            _rurality(self.is_rural),
        )


@dataclass
class Recommendation:
    """Prescriptive recommendation for one H3 cell."""

    h3_index: str
    action: str
    expected_quality_after: float
    expected_uplift: float
    estimated_cost_normalised: float
    roi_score: float  # uplift / cost, weighted
    priority_rank: int
    rationale: str
    lat: float = 0.0
    lon: float = 0.0
    is_rural: bool = False
    current_quality: float = 0.0
    state_key: str = ""

    def to_dict(self) -> dict:
        return {
            "h3_index": self.h3_index,
            "action": self.action,
            "expected_quality_after": round(self.expected_quality_after, 1),
            "expected_uplift": round(self.expected_uplift, 1),
            "estimated_cost_normalised": round(self.estimated_cost_normalised, 3),
            "roi_score": round(self.roi_score, 2),
            "priority_rank": self.priority_rank,
            "rationale": self.rationale,
            "lat": round(self.lat, 4),
            "lon": round(self.lon, 4),
            "is_rural": self.is_rural,
            "current_quality": round(self.current_quality, 1),
        }


@dataclass
class PrescriptiveReport:
    """Full prescriptive-recommendation report."""

    generated_at: str
    model_version: str = "1.0.0"
    total_cells: int = 0
    cells_with_actions: int = 0
    total_episodes_trained: int = 0
    recommendations: list[Recommendation] = field(default_factory=list)
    policy_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "model_version": self.model_version,
            "total_cells": self.total_cells,
            "cells_with_actions": self.cells_with_actions,
            "total_episodes_trained": self.total_episodes_trained,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "policy_summary": self.policy_summary,
        }


# ── Q-learning agent ─────────────────────────────────────────────────────────

class PrescriptiveAgent:
    """Tabular Q-learning agent for infrastructure-intervention recommendations.

    Workflow:
    1. ``train(cell_states)`` — simulate episodes to learn Q-values.
    2. ``recommend(cell_states)`` — pick best action per cell from learned policy.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 0.2,
        episodes: int = 500,
    ) -> None:
        if not _NP:
            raise RuntimeError("numpy is required for PrescriptiveAgent")

        self.alpha = alpha        # learning rate
        self.gamma = gamma        # discount factor
        self.epsilon = epsilon    # exploration rate (ε-greedy)
        self.episodes = episodes
        self.actions = list(Action)
        self._q: dict[str, dict[str, float]] = {}  # state_key → {action: q_value}
        self._trained_episodes = 0

    def _get_q(self, state: str, action: str) -> float:
        return self._q.get(state, {}).get(action, 0.0)

    def _set_q(self, state: str, action: str, value: float) -> None:
        self._q.setdefault(state, {})
        self._q[state][action] = value

    # ── Reward function ──────────────────────────────────────────────────
    @staticmethod
    def _reward(
        cell: CellState, action: Action,
    ) -> tuple[float, float, float]:
        """Compute (reward, uplift, cost) for taking *action* in *cell*'s state.

        Reward = (quality_uplift × rural_multiplier) / (cost + ε)
        """
        params = ACTION_PARAMS[action]
        base_uplift = params["quality_uplift"]
        cost = params["cost"]

        # Technology compatibility bonus
        tech_g = _tech_group(cell.technology)
        best_techs = [_tech_group(t) for t in params["best_for"]]
        compat = 1.3 if tech_g in best_techs else 0.8

        # Rural areas get a policy multiplier (government incentive proxy)
        rural_mult = 1.5 if cell.is_rural else 1.0

        # Quality headroom — diminishing returns near 100
        headroom = max(100 - cell.quality_score, 5) / 100
        uplift = base_uplift * compat * headroom

        # Reward
        reward = (uplift * rural_mult) / (cost + 0.01)
        return reward, uplift, cost

    # ── Train ────────────────────────────────────────────────────────────
    def train(self, cell_states: list[CellState]) -> int:
        """Train Q-table by simulating episodes over given cell states.

        Returns the number of episodes completed.
        """
        if not cell_states:
            return 0

        rng = random.Random(42)
        eps = self.epsilon

        for episode in range(self.episodes):
            # Decay epsilon over time
            eps = max(self.epsilon * (1 - episode / self.episodes), 0.01)

            for cell in cell_states:
                state = cell.state_key

                # ε-greedy action selection
                if rng.random() < eps:
                    action = rng.choice(self.actions)
                else:
                    # Exploit: best known action
                    q_vals = {a: self._get_q(state, a.value) for a in self.actions}
                    action = max(q_vals, key=q_vals.get)  # type: ignore[arg-type]

                reward, uplift, _ = self._reward(cell, action)

                # Next state after action (simplified: quality improves)
                new_quality = min(cell.quality_score + uplift, 100)
                next_state = _state_key(
                    _quality_bucket(new_quality),
                    _tech_group(cell.technology),
                    _rurality(cell.is_rural),
                )

                # Q-learning update
                best_next = max(
                    (self._get_q(next_state, a.value) for a in self.actions),
                    default=0.0,
                )
                old_q = self._get_q(state, action.value)
                new_q = old_q + self.alpha * (reward + self.gamma * best_next - old_q)
                self._set_q(state, action.value, new_q)

        self._trained_episodes += self.episodes
        logger.info(
            "PrescriptiveAgent trained — %d episodes, %d state entries",
            self._trained_episodes,
            len(self._q),
        )
        return self._trained_episodes

    # ── Recommend ────────────────────────────────────────────────────────
    def recommend(self, cell_states: list[CellState]) -> PrescriptiveReport:
        """Generate ranked prescriptive recommendations for each cell.

        If Q-table is empty (not trained), uses the reward function directly
        as a greedy fallback.
        """
        now = datetime.now(timezone.utc).isoformat()
        report = PrescriptiveReport(
            generated_at=now,
            total_cells=len(cell_states),
            total_episodes_trained=self._trained_episodes,
        )

        recommendations: list[Recommendation] = []

        for cell in cell_states:
            state = cell.state_key

            # Pick best action (trained Q or greedy fallback)
            if self._q.get(state):
                q_vals = {a: self._get_q(state, a.value) for a in self.actions}
                best_action = max(q_vals, key=q_vals.get)  # type: ignore[arg-type]
            else:
                # Greedy fallback: pick action with highest reward
                rewards = {a: self._reward(cell, a)[0] for a in self.actions}
                best_action = max(rewards, key=rewards.get)  # type: ignore[arg-type]

            _, uplift, cost = self._reward(cell, best_action)
            expected_after = min(cell.quality_score + uplift, 100)
            roi = (uplift * (1.5 if cell.is_rural else 1.0)) / (cost + 0.01)

            rationale = self._build_rationale(cell, best_action, uplift)

            if best_action != Action.MAINTAIN:
                recommendations.append(Recommendation(
                    h3_index=cell.h3_index,
                    action=best_action.value,
                    expected_quality_after=expected_after,
                    expected_uplift=uplift,
                    estimated_cost_normalised=cost,
                    roi_score=roi,
                    priority_rank=0,  # set below
                    rationale=rationale,
                    lat=cell.lat,
                    lon=cell.lon,
                    is_rural=cell.is_rural,
                    current_quality=cell.quality_score,
                    state_key=state,
                ))

        # Rank by ROI (highest first)
        recommendations.sort(key=lambda r: r.roi_score, reverse=True)
        for i, rec in enumerate(recommendations):
            rec.priority_rank = i + 1

        report.recommendations = recommendations
        report.cells_with_actions = len(recommendations)
        report.policy_summary = self._policy_summary()

        return report

    # ── Helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _build_rationale(cell: CellState, action: Action, uplift: float) -> str:
        parts: list[str] = []
        if cell.is_rural:
            parts.append("Rural area")
        else:
            parts.append("Urban area")

        bucket = _quality_bucket(cell.quality_score)
        parts.append(f"with {bucket} quality ({cell.quality_score:.0f}/100)")

        params = ACTION_PARAMS[action]
        parts.append(
            f"→ {params['description_en']}"
            f" (expected +{uplift:.0f} pts, cost index {params['cost']:.2f})"
        )
        return ". ".join(parts) + "."

    def _policy_summary(self) -> dict:
        """Summarise the learned policy: which action dominates per state type."""
        summary: dict[str, str] = {}
        for state_key, q_vals in self._q.items():
            if q_vals:
                best = max(q_vals, key=q_vals.get)  # type: ignore[arg-type]
                summary[state_key] = best
        return {"learned_policy": summary, "total_states": len(self._q)}


# ── Convenience: build CellStates from Gold data ────────────────────────────

_MAJOR_CITIES = [
    (-23.5505, -46.6333),
    (-22.9068, -43.1729),
    (-15.7939, -47.8828),
    (-12.9714, -38.5014),
    (-3.7172, -38.5434),
    (-8.0476, -34.8770),
    (-3.1190, -60.0217),
    (-25.4284, -49.2733),
]


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


def cell_states_from_gold(measurements: list[dict]) -> list[CellState]:
    """Convert Gold-layer measurements to CellState objects (grouped by H3)."""
    cells: dict[str, list[dict]] = {}
    for m in measurements:
        h3 = m.get("h3_index") or "unknown"
        cells.setdefault(h3, []).append(m)

    states: list[CellState] = []
    for h3, points in cells.items():
        if h3 == "unknown":
            continue

        qualities = [
            p.get("confidence_score")
            or p.get("quality_score", {}).get("overall_score", 50)
            for p in points
        ]
        downloads = [p.get("download_mbps") or p.get("speed_test", {}).get("download", 0) for p in points]
        uploads = [p.get("upload_mbps") or p.get("speed_test", {}).get("upload", 0) for p in points]
        latencies = [p.get("latency_ms") or p.get("speed_test", {}).get("latency", 0) for p in points]

        tech_counts: dict[str, int] = {}
        for p in points:
            tech = str(p.get("technology", "unknown")).lower()
            tech_counts[tech] = tech_counts.get(tech, 0) + 1
        dom_tech = max(tech_counts, key=tech_counts.get)  # type: ignore[arg-type]

        lats = [p.get("lat", p.get("latitude", 0)) for p in points]
        lons = [p.get("lon", p.get("longitude", 0)) for p in points]
        avg_lat = sum(lats) / len(lats)
        avg_lon = sum(lons) / len(lons)

        dist = _distance_from_city(avg_lat, avg_lon)

        states.append(CellState(
            h3_index=h3,
            quality_score=sum(qualities) / len(qualities),
            technology=dom_tech,
            is_rural=dist > 100,
            lat=avg_lat,
            lon=avg_lon,
            measurement_count=len(points),
            download_mbps=sum(downloads) / len(downloads),
            upload_mbps=sum(uploads) / len(uploads),
            latency_ms=sum(latencies) / len(latencies),
        ))

    return states
