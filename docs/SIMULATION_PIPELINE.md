# Simulation Pipeline (Research-Grade Spec + Scaffold)

This repo includes a **toy, runnable scaffold** at [simulation_pipeline.py](../simulation_pipeline.py) plus a CLI wrapper at [scripts/run_simulation.py](../scripts/run_simulation.py).

The current implementation is intentionally minimal (stable and testable), and this document outlines the **research-grade direction** for the next iterations: equations, numerical schemes, validation, and acceptance criteria.

## 1) Scope

### In-scope (next sprint)

- Make the pipeline runnable from CLI with reproducible configs and outputs.
- Define the target equations and consistent units (even if we keep a toy solver initially).
- Add validation cases that can be used as regression tests.

### Out-of-scope (until equations & validation are locked)

- Claims of physical accuracy.
- Performance optimizations (GPU, distributed, etc.).

## 2) Target Model (Pinned, v0)

We pin a **dimensionless**, **periodic** model that is stable and testable.

### Matter / antimatter fields

Two complex scalar fields $\psi_m(x,t)$ and $\psi_a(x,t)$ follow the same linear Schrödinger-like PDE:

$$ i\,\partial_t \psi = -\alpha\,\nabla^2\psi + V_{tor}(x)\,\psi - i\,\gamma\,\psi $$

Notes:
- $\alpha$ is a dispersion coefficient (dimensionless).
- $\gamma\ge 0$ is optional damping.
- This version does **not** include minimal coupling to EM potentials yet (that requires a gauge choice and is deferred).

### Charge and current (used by Maxwell)

We define a charge-like density and current-like flux:

$$ \rho = |\psi_m|^2 - |\psi_a|^2 $$
$$ \mathbf{J} = \Im\left(\psi_m^*\nabla\psi_m\right) - \Im\left(\psi_a^*\nabla\psi_a\right) $$

### EM fields

We evolve $\mathbf{E}(x,t)$ and $\mathbf{B}(x,t)$ with a Maxwell-like system:

$$ \partial_t \mathbf{E} = \nabla\times\mathbf{B} - \mathbf{J} - \sigma\,\mathbf{E} $$
$$ \partial_t \mathbf{B} = -\nabla\times\mathbf{E} $$

with constraints:

$$ \nabla\cdot\mathbf{E} = \rho, \qquad \nabla\cdot\mathbf{B} = 0 $$

We enforce these constraints numerically via a spectral projection each step.

**Important (periodic solvability):** on a periodic domain, a strictly periodic $\mathbf{E}$ field cannot satisfy Gauss’ law for a non-zero net charge. We therefore assume (and enforce) **neutrality** by removing the spatial mean of $\rho$ when applying the Gauss constraint.

## 3) Numerics (Pinned, v0)

**Goal:** a stable, testable baseline.

- **Wavefunction propagation:** Strang split-step Fourier (spectral kinetic step + real-space potential step).
- **Maxwell update:** finite-difference curl + **spectral divergence cleaning** enforcing Gauss constraints.
- **PIC:** placeholder only (deferred until interpolation/shape functions are specified).

## 4) Safety + Stability

We treat safety as numerical stability and guardrails:

- Finite checks on all state arrays.
- Bounds on $|\psi|$ and field magnitudes.
- Deterministic runs via seed.

Acceptance: simulation must stop cleanly if stability checks fail.

## 5) Validation Plan (Concrete)

### Minimal regression tests

- Shape + dtype invariants (psi fields complex, E/B real, correct grid sizes).
- State remains finite for small grids and small dt.

### Physics validation (v0)

- **Norm conservation (wave):** with $V=0$ and $\gamma=0$, the split-step update should conserve $\|\psi\|_2$ up to numerical tolerance.
- **Gauss constraints (EM):** after each EM step, spectral divergence should satisfy:
	- $\max |\nabla\cdot\mathbf{E} - \rho|$ small
	- $\max |\nabla\cdot\mathbf{B}|$ small

### Physics validation (once equations are fixed)

- Conserved quantities where applicable.
- Known analytic solutions / manufactured solutions.
- Grid convergence study on simplified scenarios.

## 6) How to Run

### CLI

From repo root:

```bash
python scripts/run_simulation.py --preset heavy
python scripts/run_simulation.py --preset smoke --save-npz
python scripts/run_simulation.py --grid 64,64,64 --steps 200 --dt 0.01
```

Outputs are written under `data/analytics/simulation_runs/`.
