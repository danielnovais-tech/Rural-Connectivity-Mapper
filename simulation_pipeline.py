"""Toy simulation pipeline.

This module implements the function skeleton provided in the prompt with a minimal,
NumPy-based time-marching loop. The numerics here are intentionally lightweight and
serve as a runnable scaffold (not a validated physics model).

Key choices:
- Periodic boundary conditions via np.roll.
- Wavefunction propagation: simple explicit update using a Laplacian + potential phase.
- EM update: simplified Maxwell-like update using curls.
- PIC and annihilation: placeholders that are safe no-ops unless particles are provided.

The public API follows the prompt's function names so other code can import and
override pieces incrementally.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np

LOGGER = logging.getLogger(__name__)


_K_CACHE: dict[tuple[int, int, int], tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
_K_CACHE_EM: dict[tuple[int, int, int], tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}


def _shape3(shape: tuple[int, ...]) -> tuple[int, int, int]:
    """Normalize a numpy shape tuple to a strict 3D shape.

    This file assumes 3D grids throughout; we keep the runtime check to fail fast
    if a non-3D array is passed.
    """

    if len(shape) != 3:
        raise ValueError(f"Expected a 3D shape, got {shape!r}")
    return (int(shape[0]), int(shape[1]), int(shape[2]))


def _k_grids(shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return spectral wave-number grids (kx, ky, kz, k2) for periodic domain.

    Uses the Fourier convention compatible with np.fft.fftn/ifftn.
    """

    shape3 = _shape3(shape)

    if shape3 in _K_CACHE:
        return _K_CACHE[shape3]

    nx, ny, nz = shape3
    kx_1d = 2.0 * np.pi * np.fft.fftfreq(nx, d=1.0)
    ky_1d = 2.0 * np.pi * np.fft.fftfreq(ny, d=1.0)
    kz_1d = 2.0 * np.pi * np.fft.fftfreq(nz, d=1.0)

    kx, ky, kz = np.meshgrid(kx_1d, ky_1d, kz_1d, indexing="ij")
    k2 = (kx**2 + ky**2 + kz**2).astype(np.float64)

    _K_CACHE[shape3] = (kx, ky, kz, k2)
    return kx, ky, kz, k2


def _k_grids_em(shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return spectral wave-number grids for EM constraint projection.

    For *real-valued* periodic fields on an even grid, the Nyquist mode corresponds
    to a pure cosine (e.g. (-1)^j) whose derivative samples to zero at grid points.
    To keep spectral derivatives consistent with real collocation (and to preserve
    real-valued corrected fields), we set the Nyquist derivative multipliers to 0.
    """

    shape3 = _shape3(shape)
    if shape3 in _K_CACHE_EM:
        return _K_CACHE_EM[shape3]

    nx, ny, nz = shape3
    kx_1d = 2.0 * np.pi * np.fft.fftfreq(nx, d=1.0)
    ky_1d = 2.0 * np.pi * np.fft.fftfreq(ny, d=1.0)
    kz_1d = 2.0 * np.pi * np.fft.fftfreq(nz, d=1.0)

    if nx % 2 == 0:
        kx_1d[nx // 2] = 0.0
    if ny % 2 == 0:
        ky_1d[ny // 2] = 0.0
    if nz % 2 == 0:
        kz_1d[nz // 2] = 0.0

    kx, ky, kz = np.meshgrid(kx_1d, ky_1d, kz_1d, indexing="ij")
    k2 = (kx**2 + ky**2 + kz**2).astype(np.float64)

    _K_CACHE_EM[shape3] = (kx, ky, kz, k2)
    return kx, ky, kz, k2


def _project_rho_for_gauss(rho: np.ndarray) -> np.ndarray:
    """Project rho onto a compatible subspace for periodic Gauss constraint.

    For a *real* periodic E-field, the spectral divergence operator cannot
    represent arbitrary real rho at the self-conjugate Fourier corner modes
    (0/Nyquist combinations). We therefore:
    - remove the mean (net charge) and
    - zero the self-conjugate corner modes in Fourier space.

    This makes the constraint solve well-posed and keeps the corrected fields real.
    """

    rho0 = rho.astype(np.float64, copy=False)
    rho0 = rho0 - float(np.mean(rho0))

    shape = _shape3(tuple(int(v) for v in rho0.shape))
    _kx, _ky, _kz, k2 = _k_grids_em(shape)

    rho_hat = np.fft.fftn(rho0)

    # Remove any components in the nullspace of the EM divergence operator.
    # This includes the mean and the self-conjugate corner modes on even grids.
    rho_hat[k2 == 0.0] = 0.0
    return np.fft.ifftn(rho_hat).real.astype(np.float64)


def _divergence_spectral(vec_field: np.ndarray) -> np.ndarray:
    """Spectral divergence of a 3-vector field with shape (3, Nx, Ny, Nz)."""

    shape = tuple(int(v) for v in vec_field.shape[1:])
    kx, ky, kz, _k2 = _k_grids_em(shape)

    fx_hat = np.fft.fftn(vec_field[0])
    fy_hat = np.fft.fftn(vec_field[1])
    fz_hat = np.fft.fftn(vec_field[2])

    div_hat = 1j * (kx * fx_hat + ky * fy_hat + kz * fz_hat)
    div = np.fft.ifftn(div_hat).real
    return div


def _enforce_gauss_constraints(
    e_field: np.ndarray,
    b_field: np.ndarray,
    rho: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Project fields to satisfy Gauss constraints under periodic BCs.

    Enforces:
    - ∇·E = rho
    - ∇·B = 0

    via spectral Poisson solves.
    """

    # Periodic real-valued fields require rho to be projected into the representable
    # subspace of the divergence operator.
    rho = _project_rho_for_gauss(rho)

    shape = tuple(int(v) for v in rho.shape)
    kx, ky, kz, k2 = _k_grids_em(shape)

    # FFTs
    ex_hat = np.fft.fftn(e_field[0])
    ey_hat = np.fft.fftn(e_field[1])
    ez_hat = np.fft.fftn(e_field[2])
    bx_hat = np.fft.fftn(b_field[0])
    by_hat = np.fft.fftn(b_field[1])
    bz_hat = np.fft.fftn(b_field[2])
    rho_hat = np.fft.fftn(rho)

    # Enforce constraints in Fourier space by removing/setting the longitudinal
    # component along k.
    #
    # With numpy FFT conventions, spectral divergence is:
    #   div_hat = i * (k·F_hat)
    # so Gauss's law div(E) = rho becomes:
    #   k·E_hat = -i * rho_hat

    k_dot_e = kx * ex_hat + ky * ey_hat + kz * ez_hat
    k_dot_b = kx * bx_hat + ky * by_hat + kz * bz_hat

    target_k_dot_e = -1j * rho_hat

    delta_e = k_dot_e - target_k_dot_e
    delta_b = k_dot_b

    mask = k2 != 0.0
    scale_e = np.zeros_like(delta_e)
    scale_b = np.zeros_like(delta_b)
    scale_e[mask] = delta_e[mask] / k2[mask]
    scale_b[mask] = delta_b[mask] / k2[mask]

    ex_hat = ex_hat - kx * scale_e
    ey_hat = ey_hat - ky * scale_e
    ez_hat = ez_hat - kz * scale_e

    bx_hat = bx_hat - kx * scale_b
    by_hat = by_hat - ky * scale_b
    bz_hat = bz_hat - kz * scale_b

    e_corr = np.stack(
        [
            np.fft.ifftn(ex_hat).real,
            np.fft.ifftn(ey_hat).real,
            np.fft.ifftn(ez_hat).real,
        ],
        axis=0,
    ).astype(np.float64)
    b_corr = np.stack(
        [
            np.fft.ifftn(bx_hat).real,
            np.fft.ifftn(by_hat).real,
            np.fft.ifftn(bz_hat).real,
        ],
        axis=0,
    ).astype(np.float64)

    return e_corr, b_corr


@dataclass(frozen=True)
class Domain:
    grid: tuple[int, int, int]
    spacing: tuple[float, float, float]
    coords: tuple[np.ndarray, np.ndarray, np.ndarray]


@dataclass(frozen=True)
class ToroidalPotentialParams:
    v0: float = 1.0
    r0: float = 0.35
    sigma: float = 0.12


@dataclass(frozen=True)
class SimulationConfig:
    dt: float
    time_steps: int
    grid: tuple[int, int, int] = (100, 100, 100)
    spacing: tuple[float, float, float] = (1.0, 1.0, 1.0)
    wave_alpha: float = 0.25
    wave_damping: float = 0.0
    report_every: int = 10
    max_abs_psi: float = 1e6
    max_abs_field: float = 1e6


def _as_params(obj: Any) -> ToroidalPotentialParams:
    if isinstance(obj, ToroidalPotentialParams):
        return obj
    if isinstance(obj, dict):
        return ToroidalPotentialParams(
            v0=float(obj.get("v0", 1.0)),
            r0=float(obj.get("r0", 0.35)),
            sigma=float(obj.get("sigma", 0.12)),
        )
    raise TypeError("V_tor_params must be a dict or ToroidalPotentialParams")


def initialize_domain(dimensions: tuple[int, ...], grid: tuple[int, ...]):
    """Set up a spatial grid domain.

    Only 3D is supported by this scaffold.
    """

    if tuple(dimensions) != (3,):
        raise ValueError("This scaffold supports dimensions=(3,) only")
    if len(grid) != 3:
        raise ValueError("grid must be a 3-tuple like (Nx, Ny, Nz)")

    nx, ny, nz = (int(grid[0]), int(grid[1]), int(grid[2]))
    # Normalized coordinates in [-0.5, 0.5)
    x = (np.arange(nx) / nx) - 0.5
    y = (np.arange(ny) / ny) - 0.5
    z = (np.arange(nz) / nz) - 0.5
    xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")

    return Domain(grid=(nx, ny, nz), spacing=(1.0, 1.0, 1.0), coords=(xx, yy, zz))


def initialize_potentials(v_tor_params):
    """Define a simple toroidal potential V_tor on the domain grid."""

    params = _as_params(v_tor_params)

    # We interpret r0/sigma in normalized coordinate units.
    # This function returns a callable so that callers can swap in custom domains.
    def v_tor(domain: Domain) -> np.ndarray:
        xx, yy, zz = domain.coords
        rr = np.sqrt(xx**2 + yy**2)
        # Ring-shaped Gaussian around radius r0 in x-y plane
        torus = np.exp(-(((rr - params.r0) ** 2) + (zz**2)) / (2 * params.sigma**2))
        return params.v0 * torus

    return v_tor


def initialize_wavefunctions(initial_conditions):
    """Create psi_m and psi_anti wavefunctions as complex numpy arrays."""

    if not isinstance(initial_conditions, dict):
        initial_conditions = {} if initial_conditions is None else dict(initial_conditions)

    grid = tuple(int(v) for v in initial_conditions.get("grid", (100, 100, 100)))
    nx, ny, nz = grid

    seed = initial_conditions.get("seed", 0)
    rng = np.random.default_rng(seed)

    amp_m = float(initial_conditions.get("amp_m", 1.0))
    amp_anti = float(initial_conditions.get("amp_anti", 1.0))

    # Default: slightly perturbed constant fields.
    psi_m = (amp_m * (1.0 + 1e-3 * rng.standard_normal(grid))).astype(np.complex128)
    psi_anti = (amp_anti * (1.0 + 1e-3 * rng.standard_normal(grid))).astype(np.complex128)

    # Optional: Gaussian packets (center in normalized coords)
    packet = initial_conditions.get("gaussian_packet")
    if isinstance(packet, dict):
        center = packet.get("center", (0.0, 0.0, 0.0))
        width = float(packet.get("width", 0.12))

        x = (np.arange(nx) / nx) - 0.5
        y = (np.arange(ny) / ny) - 0.5
        z = (np.arange(nz) / nz) - 0.5
        xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")

        cx, cy, cz = (float(center[0]), float(center[1]), float(center[2]))
        gauss = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2 + (zz - cz) ** 2) / (2 * width**2)))
        psi_m = (amp_m * gauss).astype(np.complex128)
        psi_anti = (amp_anti * gauss).astype(np.complex128)

    return psi_m, psi_anti


def initialize_em_fields():
    """Initialize E and B fields as 3-component arrays."""

    # Caller can resize later once a domain exists.
    e_field = np.zeros((3, 1, 1, 1), dtype=np.float64)
    b_field = np.zeros((3, 1, 1, 1), dtype=np.float64)
    return e_field, b_field


def initialize_EM_fields():  # noqa: N802
    """Backwards-compatible name from the prompt."""

    return initialize_em_fields()


def _laplacian_periodic(u: np.ndarray) -> np.ndarray:
    return (
        np.roll(u, 1, axis=0)
        + np.roll(u, -1, axis=0)
        + np.roll(u, 1, axis=1)
        + np.roll(u, -1, axis=1)
        + np.roll(u, 1, axis=2)
        + np.roll(u, -1, axis=2)
        - 6.0 * u
    )


def _grad_periodic(u: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dx = 0.5 * (np.roll(u, -1, axis=0) - np.roll(u, 1, axis=0))
    dy = 0.5 * (np.roll(u, -1, axis=1) - np.roll(u, 1, axis=1))
    dz = 0.5 * (np.roll(u, -1, axis=2) - np.roll(u, 1, axis=2))
    return dx, dy, dz


def _curl_periodic(field: np.ndarray) -> np.ndarray:
    """Curl of a 3-vector field with periodic BCs.

    field has shape (3, Nx, Ny, Nz).
    """

    fx, fy, fz = field[0], field[1], field[2]
    dfy_dz = 0.5 * (np.roll(fy, -1, axis=2) - np.roll(fy, 1, axis=2))
    dfz_dy = 0.5 * (np.roll(fz, -1, axis=1) - np.roll(fz, 1, axis=1))

    dfz_dx = 0.5 * (np.roll(fz, -1, axis=0) - np.roll(fz, 1, axis=0))
    dfx_dz = 0.5 * (np.roll(fx, -1, axis=2) - np.roll(fx, 1, axis=2))

    dfx_dy = 0.5 * (np.roll(fx, -1, axis=1) - np.roll(fx, 1, axis=1))
    dfy_dx = 0.5 * (np.roll(fy, -1, axis=0) - np.roll(fy, 1, axis=0))

    curl = np.empty_like(field)
    curl[0] = dfz_dy - dfy_dz
    curl[1] = dfx_dz - dfz_dx
    curl[2] = dfy_dx - dfx_dy
    return curl


def propagate_wavefunction(psi, v_tor, em_fields, dt):
    r"""Propagate psi forward by one time step.

    Pinned model (dimensionless):

    $$ i\,\partial_t \psi = -\alpha\,\nabla^2\psi + V\,\psi - i\,\gamma\,\psi $$

    with periodic boundary conditions.

    Numerics: Strang split-step Fourier.
    """

    _e_field, _b_field = em_fields

    if isinstance(dt, dict):
        raise TypeError("dt must be a float")

    alpha = 0.25
    gamma = 0.0
    potential = v_tor

    shape = tuple(int(v) for v in psi.shape)
    _kx, _ky, _kz, k2 = _k_grids(shape)

    half_v = np.exp(-1j * potential * (dt / 2.0))
    kinetic = np.exp(-1j * alpha * k2 * dt)
    damp = np.exp(-gamma * dt)

    psi1 = psi * half_v
    psi_hat = np.fft.fftn(psi1)
    psi_hat = psi_hat * kinetic
    psi2 = np.fft.ifftn(psi_hat)
    psi3 = psi2 * half_v
    psi_next = psi3 * damp
    return psi_next


def compute_density_currents(psi_m, psi_anti):
    """Extract charge-like density rho and current-like J from wavefunctions."""

    rho_m = np.abs(psi_m) ** 2
    rho_a = np.abs(psi_anti) ** 2
    rho = rho_m - rho_a

    # J ~ Im(conj(psi) * grad(psi))
    def current(psi: np.ndarray) -> np.ndarray:
        dpsi_dx, dpsi_dy, dpsi_dz = _grad_periodic(psi)
        conj = np.conjugate(psi)
        jx = np.imag(conj * dpsi_dx)
        jy = np.imag(conj * dpsi_dy)
        jz = np.imag(conj * dpsi_dz)
        return np.stack([jx, jy, jz], axis=0)

    j_field = current(psi_m) - current(psi_anti)
    return rho.astype(np.float64), j_field.astype(np.float64)


def update_em_fields(e_field, b_field, rho, j_field, dt):
    r"""Update E and B using a Maxwell-like update + constraint cleaning.

    Pinned model (dimensionless):

    $$ \partial_t \mathbf{E} = \nabla\times\mathbf{B} - \mathbf{J} - \sigma\,\mathbf{E} $$
    $$ \partial_t \mathbf{B} = -\nabla\times\mathbf{E} $$

    with constraints enforced each step:

    $$ \nabla\cdot\mathbf{E} = \rho, \qquad \nabla\cdot\mathbf{B} = 0 $$
    """

    # Resize fields lazily to match rho if needed.
    if e_field.shape[1:] != rho.shape:
        e_field = np.zeros((3,) + rho.shape, dtype=np.float64)
    if b_field.shape[1:] != rho.shape:
        b_field = np.zeros((3,) + rho.shape, dtype=np.float64)

    curl_b = _curl_periodic(b_field)
    curl_e = _curl_periodic(e_field)

    sigma = 0.0

    # In normalized units: dE/dt = curl(B) - J - sigma*E, dB/dt = -curl(E)
    e_next = e_field + dt * (curl_b - j_field - sigma * e_field)
    b_next = b_field + dt * (-curl_e)

    # Enforce Gauss constraints via spectral projection.
    e_next, b_next = _enforce_gauss_constraints(e_next, b_next, rho)

    return e_next, b_next


def pic_push(particles, e_field, b_field, dt):
    """Particle-in-cell push (placeholder).

    Expected particle format (optional):
    - dict with keys: pos (3,), vel (3,), q, m
    """

    if not particles:
        return particles

    particles_next: list[dict[str, Any]] = []
    e0 = e_field.reshape(3, -1).mean(axis=1)
    b0 = b_field.reshape(3, -1).mean(axis=1)

    for p in particles:
        pos = np.asarray(p.get("pos", (0.0, 0.0, 0.0)), dtype=float)
        vel = np.asarray(p.get("vel", (0.0, 0.0, 0.0)), dtype=float)
        q = float(p.get("q", 1.0))
        m = float(p.get("m", 1.0))

        # Simple non-relativistic Lorentz acceleration using average field.
        acc = (q / m) * (e0 + np.cross(vel, b0))
        vel_next = vel + dt * acc
        pos_next = pos + dt * vel_next

        p2 = dict(p)
        p2["pos"] = pos_next
        p2["vel"] = vel_next
        particles_next.append(p2)

    return particles_next


def handle_annihilation(psi_m, psi_anti, particles):
    """Stochastic annihilation kernel (toy).

    We reduce overlapping density slightly to mimic annihilation without randomness.
    """

    overlap = np.minimum(np.abs(psi_m) ** 2, np.abs(psi_anti) ** 2)
    # Small sink term proportional to overlap.
    k = 1e-3
    sink = np.exp(-k * overlap)
    psi_m2 = psi_m * sink
    psi_anti2 = psi_anti * sink

    # Optional: remove particles with tiny kinetic energy.
    if particles:
        kept: list[dict[str, Any]] = []
        for p in particles:
            vel = np.asarray(p.get("vel", (0.0, 0.0, 0.0)), dtype=float)
            if float(np.dot(vel, vel)) > 1e-12:
                kept.append(p)
        particles = kept

    return psi_m2, psi_anti2, particles


def controller_observe_and_compute(psi_m, psi_anti, e_field, b_field):
    """Feedback control logic (toy).

    Returns a dict of control signals that other code can interpret.
    """

    norm_m = float(np.mean(np.abs(psi_m) ** 2))
    norm_a = float(np.mean(np.abs(psi_anti) ** 2))
    e_mag = float(np.mean(np.linalg.norm(e_field.reshape(3, -1), axis=0)))
    b_mag = float(np.mean(np.linalg.norm(b_field.reshape(3, -1), axis=0)))

    # Toy: aim to keep average norms near 1.0.
    gain = 0.05
    scale = 1.0 - gain * ((norm_m + norm_a) - 2.0)

    return {
        "field_scale": float(np.clip(scale, 0.5, 1.5)),
        "e_target": e_mag,
        "b_target": b_mag,
    }


def apply_control(control_signals):
    """Adjust field parameters (placeholder).

    This scaffold is stateless; callers can override and apply the returned
    signals inside run_simulation.
    """

    _ = control_signals


def log_state(t, psi_m, psi_anti, e_field, b_field, energies):
    """Diagnostics and monitoring."""

    if t == 0 or (t % 10 == 0):
        LOGGER.info(
            "t=%s mean|psi_m|^2=%.6g mean|psi_a|^2=%.6g mean|E|=%.6g mean|B|=%.6g",
            t,
            energies.get("mean_rho_m", float(np.mean(np.abs(psi_m) ** 2))),
            energies.get("mean_rho_a", float(np.mean(np.abs(psi_anti) ** 2))),
            energies.get(
                "mean_E",
                float(np.mean(np.linalg.norm(e_field.reshape(3, -1), axis=0))),
            ),
            energies.get(
                "mean_B",
                float(np.mean(np.linalg.norm(b_field.reshape(3, -1), axis=0))),
            ),
        )


def safety_violation_detected(
    *,
    psi_m: np.ndarray | None = None,
    psi_anti: np.ndarray | None = None,
    e_field: np.ndarray | None = None,
    b_field: np.ndarray | None = None,
    max_abs_psi: float = 1e6,
    max_abs_field: float = 1e6,
) -> bool:
    """Stability checks."""

    arrays: Iterable[np.ndarray] = [a for a in (psi_m, psi_anti, e_field, b_field) if a is not None]
    for a in arrays:
        if not np.isfinite(a).all():
            return True

    if psi_m is not None and float(np.max(np.abs(psi_m))) > max_abs_psi:
        return True
    if psi_anti is not None and float(np.max(np.abs(psi_anti))) > max_abs_psi:
        return True

    if e_field is not None and float(np.max(np.abs(e_field))) > max_abs_field:
        return True
    if b_field is not None and float(np.max(np.abs(b_field))) > max_abs_field:
        return True

    return False


def trigger_safe_shutdown():
    """Emergency stop."""

    LOGGER.error("Safe shutdown triggered")


def run_simulation(time_steps, dt, initial_conditions, v_tor_params):
    """Run the simulation main loop.

    Returns a dict with final state plus a lightweight history.
    """

    logging.basicConfig(level=logging.INFO)

    grid = tuple(int(v) for v in initial_conditions.get("grid", (100, 100, 100)))
    domain = initialize_domain(dimensions=(3,), grid=grid)

    v_tor_fn = initialize_potentials(v_tor_params)
    v_tor = v_tor_fn(domain)

    psi_m, psi_anti = initialize_wavefunctions({**initial_conditions, "grid": grid})

    e_field, b_field = initialize_EM_fields()
    # Ensure correct sizing from the first step.
    e_field = np.zeros((3,) + grid, dtype=np.float64)
    b_field = np.zeros((3,) + grid, dtype=np.float64)

    particles = list(initial_conditions.get("particles", []))

    history: list[dict[str, float]] = []

    for t in range(int(time_steps)):
        psi_m = propagate_wavefunction(psi_m, v_tor, (e_field, b_field), float(dt))
        psi_anti = propagate_wavefunction(
            psi_anti,
            v_tor,
            (e_field, b_field),
            float(dt),
        )

        rho, j_field = compute_density_currents(psi_m, psi_anti)
        e_field, b_field = update_em_fields(
            e_field,
            b_field,
            rho,
            j_field,
            float(dt),
        )

        particles = pic_push(particles, e_field, b_field, float(dt))
        psi_m, psi_anti, particles = handle_annihilation(psi_m, psi_anti, particles)

        control_signals = controller_observe_and_compute(
            psi_m,
            psi_anti,
            e_field,
            b_field,
        )
        apply_control(control_signals)

        energies = {
            "mean_rho_m": float(np.mean(np.abs(psi_m) ** 2)),
            "mean_rho_a": float(np.mean(np.abs(psi_anti) ** 2)),
            "mean_E": float(np.mean(np.linalg.norm(e_field.reshape(3, -1), axis=0))),
            "mean_B": float(np.mean(np.linalg.norm(b_field.reshape(3, -1), axis=0))),
        }
        history.append(energies)

        log_state(t, psi_m, psi_anti, e_field, b_field, energies=energies)

        if safety_violation_detected(
            psi_m=psi_m,
            psi_anti=psi_anti,
            e_field=e_field,
            b_field=b_field,
        ):
            trigger_safe_shutdown()
            break

    return {
        "psi_m": psi_m,
        "psi_anti": psi_anti,
        "E": e_field,
        "B": b_field,
        "particles": particles,
        "history": history,
    }


if __name__ == "__main__":
    # Small smoke run to validate the scaffold.
    result = run_simulation(
        time_steps=20,
        dt=0.01,
        initial_conditions={"grid": (32, 32, 32), "seed": 0},
        v_tor_params={"v0": 1.0, "r0": 0.25, "sigma": 0.10},
    )
    LOGGER.info("Done. history_len=%s", len(result["history"]))
