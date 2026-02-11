#!/usr/bin/env python3
"""CLI script to run the toy simulation pipeline.

This wraps [simulation_pipeline.py](../simulation_pipeline.py) with a repo-style
`scripts/` entrypoint similar to `scripts/run_pipeline.py`.

By default it writes a small JSON summary (history + config). Saving full fields
can be enabled with `--save-npz` (can be large for heavy grids).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import simulation_pipeline as sim


def _parse_grid(value: str) -> tuple[int, int, int]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("grid must be like '128,128,128'")
    try:
        nx, ny, nz = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("grid values must be integers") from exc
    if nx <= 0 or ny <= 0 or nz <= 0:
        raise argparse.ArgumentTypeError("grid values must be positive")
    return nx, ny, nz


def _preset(preset: str) -> tuple[tuple[int, int, int], int, float]:
    preset = preset.lower().strip()
    if preset == "smoke":
        return (32, 32, 32), 50, 0.01
    if preset == "medium":
        return (64, 64, 64), 200, 0.01
    if preset == "heavy":
        return (128, 128, 128), 500, 0.005
    raise ValueError("Unknown preset")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the toy simulation pipeline")
    parser.add_argument(
        "--preset",
        choices=["smoke", "medium", "heavy"],
        default="heavy",
        help="Default run preset (default: heavy)",
    )
    parser.add_argument(
        "--grid",
        type=_parse_grid,
        default=None,
        help="Override grid, e.g. 128,128,128",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="Override number of time steps",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=None,
        help="Override time step size",
    )
    parser.add_argument("--seed", type=int, default=0, help="RNG seed")
    parser.add_argument(
        "--v0",
        type=float,
        default=1.0,
        help="Toroidal potential amplitude",
    )
    parser.add_argument("--r0", type=float, default=0.25, help="Toroidal radius")
    parser.add_argument("--sigma", type=float, default=0.10, help="Toroidal width")
    parser.add_argument(
        "--output-dir",
        default=str(Path("data") / "analytics" / "simulation_runs"),
        help="Directory where run artifacts are written",
    )
    parser.add_argument(
        "--save-npz",
        action="store_true",
        help="Also save fields to a compressed .npz (can be large)",
    )

    args = parser.parse_args()

    preset_grid, preset_steps, preset_dt = _preset(args.preset)
    grid = args.grid or preset_grid
    steps = int(args.steps or preset_steps)
    dt = float(args.dt or preset_dt)


    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.output_dir) / f"run_{run_id}_{args.preset}"
    out_dir.mkdir(parents=True, exist_ok=True)

    initial_conditions = {
        "grid": grid,
        "seed": args.seed,
    }
    v_tor_params = {
        "v0": args.v0,
        "r0": args.r0,
        "sigma": args.sigma,
    }

    result = sim.run_simulation(
        time_steps=steps,
        dt=dt,
        initial_conditions=initial_conditions,
        v_tor_params=v_tor_params,
    )

    history = result["history"]
    summary = {
        "run_id": run_id,
        "preset": args.preset,
        "grid": list(grid),
        "steps_requested": steps,
        "dt": dt,
        "v_tor_params": v_tor_params,
        "history_len": len(history),
        "history": history,
        "final": {
            "mean_rho_m": history[-1]["mean_rho_m"] if history else None,
            "mean_rho_a": history[-1]["mean_rho_a"] if history else None,
            "mean_E": history[-1]["mean_E"] if history else None,
            "mean_B": history[-1]["mean_B"] if history else None,
            "particles": len(result["particles"]),
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if args.save_npz:
        # Note: these arrays can be large for heavy grids.
        npz_path = out_dir / "fields.npz"
        import numpy as np

        np.savez_compressed(
            npz_path,
            psi_m=result["psi_m"],
            psi_anti=result["psi_anti"],
            E=result["E"],
            B=result["B"],
        )

    print("✅ Simulation completed")
    print(f"Output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
