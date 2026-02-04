r"""Stress test harness for Rural Connectivity Mapper.

Goals:
- Generate large synthetic datasets to probe scalability.
- Simulate flaky/slow network conditions (via mocking) for geocoding.
- Time key pipeline stages and write artifacts.

This is intentionally a script (not part of pytest) to avoid slowing CI.

Usage examples:
    ./.venv/Scripts/python.exe scripts/stress/run_stress.py --points 50000
    ./.venv/Scripts/python.exe scripts/stress/run_stress.py --points 200000 --geocode-samples 2000 --delay-ms 50
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict
from unittest.mock import Mock, patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
os.chdir(_REPO_ROOT)

from geopy.exc import GeocoderQuotaExceeded, GeocoderTimedOut, GeocoderUnavailable  # noqa: E402

from src.utils.analysis_utils import analyze_temporal_evolution  # noqa: E402
from src.utils.export_utils import export_ecosystem_bundle  # noqa: E402
from src.utils.geocoding_utils import geocode_address, geocode_coordinates  # noqa: E402
from src.utils.report_utils import generate_report  # noqa: E402


@dataclass
class Timing:
    label: str
    seconds: float


def _now_iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def generate_synthetic_points(
    *,
    count: int,
    seed: int,
    providers: list[str],
    country_center: tuple[float, float] = (-15.78, -47.93),
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    base_time = datetime(2026, 1, 1, 0, 0, 0)

    center_lat, center_lon = country_center
    points: list[dict[str, Any]] = []

    for i in range(count):
        provider = providers[i % len(providers)]

        # Rough spread around the center (~few degrees).
        lat = center_lat + rng.uniform(-6.0, 6.0)
        lon = center_lon + rng.uniform(-8.0, 8.0)

        # Simulated network metrics
        download = max(1.0, rng.gauss(80.0, 30.0))
        upload = max(0.5, rng.gauss(15.0, 6.0))
        latency = max(1.0, rng.gauss(40.0, 15.0))
        jitter = max(0.0, rng.gauss(6.0, 3.0))
        packet_loss = max(0.0, min(5.0, rng.gauss(0.4, 0.6)))

        # Simple quality score model
        speed_score = min(100.0, (download / 150.0) * 100.0)
        latency_score = max(0.0, 100.0 - latency)
        stability_score = max(0.0, 100.0 - (jitter * 3.0) - (packet_loss * 10.0))
        overall = round((0.55 * speed_score + 0.25 * latency_score + 0.20 * stability_score), 1)

        ts = base_time + timedelta(minutes=i % (60 * 24 * 30))

        points.append(
            {
                "id": f"synthetic-{i}",
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "provider": provider,
                "timestamp": _now_iso(ts),
                "speed_test": {
                    "download": round(download, 2),
                    "upload": round(upload, 2),
                    "latency": round(latency, 2),
                    "jitter": round(jitter, 2),
                    "packet_loss": round(packet_loss, 3),
                    "stability": round(max(0.0, min(100.0, stability_score)), 1),
                },
                "quality_score": {
                    "overall_score": overall,
                    "rating": "Excellent"
                    if overall >= 80
                    else "Good"
                    if overall >= 65
                    else "Fair"
                    if overall >= 50
                    else "Poor",
                },
            }
        )

    return points


def _timed(label: str, fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, Timing(label=label, seconds=time.perf_counter() - start)


class FlakyGeocoder:
    def __init__(
        self,
        *,
        rng: random.Random,
        delay_ms: int,
        p_timeout: float,
        p_quota: float,
        p_unavailable: float,
        p_none: float,
    ):
        self._rng = rng
        self._delay = max(0.0, delay_ms / 1000.0)
        self._p_timeout = p_timeout
        self._p_quota = p_quota
        self._p_unavailable = p_unavailable
        self._p_none = p_none

    def _maybe_delay(self):
        if self._delay > 0:
            time.sleep(self._delay)

    def reverse(self, coords: str, timeout: Any = 10, exactly_one: bool = True):
        self._maybe_delay()
        roll = self._rng.random()

        if roll < self._p_timeout:
            raise GeocoderTimedOut("Simulated timeout")
        roll -= self._p_timeout

        if roll < self._p_quota:
            raise GeocoderQuotaExceeded("Simulated quota exceeded")
        roll -= self._p_quota

        if roll < self._p_unavailable:
            raise GeocoderUnavailable("Simulated service unavailable")
        roll -= self._p_unavailable

        if roll < self._p_none:
            return None

        loc = Mock()
        loc.address = f"Simulated address for {coords}"
        return loc

    def geocode(self, address: str, timeout: Any = 10, exactly_one: bool = True):
        self._maybe_delay()
        roll = self._rng.random()

        if roll < self._p_timeout:
            raise GeocoderTimedOut("Simulated timeout")
        roll -= self._p_timeout

        if roll < self._p_quota:
            raise GeocoderQuotaExceeded("Simulated quota exceeded")
        roll -= self._p_quota

        if roll < self._p_unavailable:
            raise GeocoderUnavailable("Simulated service unavailable")
        roll -= self._p_unavailable

        if roll < self._p_none:
            return None

        loc = Mock()
        loc.latitude = -23.5505
        loc.longitude = -46.6333
        return loc


class GeocodeStressCounters(TypedDict):
    reverse_ok: int
    reverse_none: int
    reverse_fail: int
    forward_ok: int
    forward_none: int
    forward_fail: int
    seconds: float
    samples: int


def stress_geocoding(
    *,
    rng: random.Random,
    output_dir: Path,
    geocode_samples: int,
    delay_ms: int,
    p_timeout: float,
    p_quota: float,
    p_unavailable: float,
    p_none: float,
):
    flaky = FlakyGeocoder(
        rng=rng,
        delay_ms=delay_ms,
        p_timeout=p_timeout,
        p_quota=p_quota,
        p_unavailable=p_unavailable,
        p_none=p_none,
    )

    counters: GeocodeStressCounters = {
        "reverse_ok": 0,
        "reverse_none": 0,
        "reverse_fail": 0,
        "forward_ok": 0,
        "forward_none": 0,
        "forward_fail": 0,
        "seconds": 0.0,
        "samples": geocode_samples,
    }

    # Avoid the built-in 1 req/sec limiter during stress runs.
    with patch("src.utils.geocoding_utils._wait_for_rate_limit", lambda: None):
        with patch("src.utils.geocoding_utils.geolocator.reverse", side_effect=flaky.reverse):
            with patch("src.utils.geocoding_utils.geolocator.geocode", side_effect=flaky.geocode):
                start = time.perf_counter()
                for i in range(geocode_samples):
                    # Alternate reverse + forward
                    if i % 2 == 0:
                        addr = geocode_coordinates(-23.5505, -46.6333, max_retries=2)
                        if addr is None:
                            counters["reverse_none"] += 1
                        else:
                            counters["reverse_ok"] += 1
                    else:
                        coords = geocode_address("São Paulo, Brazil", max_retries=2)
                        if coords is None:
                            counters["forward_none"] += 1
                        else:
                            counters["forward_ok"] += 1
                elapsed = time.perf_counter() - start

    counters["seconds"] = round(elapsed, 4)
    counters["samples"] = geocode_samples
    (output_dir / "geocoding_stress.json").write_text(json.dumps(counters, indent=2), encoding="utf-8")

    return Timing(label="geocoding_stress", seconds=elapsed), counters


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--points", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=str, default="stress_artifacts")

    # Geocoding/network simulation knobs
    parser.add_argument("--geocode-samples", type=int, default=1000)
    parser.add_argument("--delay-ms", type=int, default=25)
    parser.add_argument("--p-timeout", type=float, default=0.05)
    parser.add_argument("--p-quota", type=float, default=0.01)
    parser.add_argument("--p-unavailable", type=float, default=0.03)
    parser.add_argument("--p-none", type=float, default=0.05)

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    providers = ["Starlink", "Claro", "Viasat", "HughesNet"]

    timings: list[Timing] = []

    data, t = _timed(
        "generate_data",
        generate_synthetic_points,
        count=args.points,
        seed=args.seed,
        providers=providers,
    )
    timings.append(t)

    # Persist dataset sample and basic stats
    (output_dir / "dataset_meta.json").write_text(
        json.dumps(
            {
                "points": args.points,
                "providers": providers,
                "seed": args.seed,
                "python": sys.version,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "dataset_head.json").write_text(json.dumps(data[:20], indent=2), encoding="utf-8")

    analysis, t = _timed("analyze_temporal_evolution", analyze_temporal_evolution, data)
    timings.append(t)
    (output_dir / "analysis_summary.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    # Export bundle (writes files); keep it within output_dir
    export_dir = output_dir / "ecosystem_bundle"
    _, t = _timed("export_ecosystem_bundle", export_ecosystem_bundle, data, str(export_dir))
    timings.append(t)

    # Generate a report (txt) to ensure report code scales with big datasets
    report_path = output_dir / "report.txt"
    with patch("src.utils.report_utils.COLORAMA_AVAILABLE", False):
        _, t = _timed(
            "generate_report_txt",
            generate_report,
            data,
            "txt",
            str(report_path),
            "en",
        )
    timings.append(t)

    # Network condition simulation (mocked) - independent from dataset size
    rng = random.Random(args.seed)
    t_geo, geo_stats = stress_geocoding(
        rng=rng,
        output_dir=output_dir,
        geocode_samples=args.geocode_samples,
        delay_ms=args.delay_ms,
        p_timeout=args.p_timeout,
        p_quota=args.p_quota,
        p_unavailable=args.p_unavailable,
        p_none=args.p_none,
    )
    timings.append(t_geo)

    (output_dir / "timings.json").write_text(
        json.dumps(
            {"timings": [{"label": x.label, "seconds": round(x.seconds, 4)} for x in timings], "geocoding": geo_stats},
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n=== Stress run complete ===")
    for t in timings:
        print(f"{t.label:28s} {t.seconds:8.3f}s")
    print(f"Artifacts: {output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
