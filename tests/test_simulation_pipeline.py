import numpy as np

import simulation_pipeline as sim


def test_initialize_potentials_shape():
    domain = sim.initialize_domain(dimensions=(3,), grid=(8, 8, 8))
    v_tor_fn = sim.initialize_potentials({"v0": 1.0, "r0": 0.25, "sigma": 0.10})
    v = v_tor_fn(domain)
    assert v.shape == (8, 8, 8)
    assert np.isfinite(v).all()


def test_run_simulation_smoke_shapes_and_finite():
    result = sim.run_simulation(
        time_steps=3,
        dt=0.01,
        initial_conditions={"grid": (8, 8, 8), "seed": 0},
        v_tor_params={"v0": 1.0, "r0": 0.25, "sigma": 0.10},
    )

    assert result["psi_m"].shape == (8, 8, 8)
    assert result["psi_anti"].shape == (8, 8, 8)
    assert result["E"].shape == (3, 8, 8, 8)
    assert result["B"].shape == (3, 8, 8, 8)

    assert np.isfinite(result["psi_m"]).all()
    assert np.isfinite(result["psi_anti"]).all()
    assert np.isfinite(result["E"]).all()
    assert np.isfinite(result["B"]).all()

    assert len(result["history"]) >= 1


def test_safety_violation_detects_nan():
    psi = np.zeros((4, 4, 4), dtype=np.complex128)
    psi[0, 0, 0] = np.nan + 0j
    assert sim.safety_violation_detected(psi_m=psi)


def test_wave_norm_conservation_free_case():
    grid = (16, 16, 16)
    rng = np.random.default_rng(0)
    psi = (rng.standard_normal(grid) + 1j * rng.standard_normal(grid)).astype(np.complex128)
    psi = psi / np.sqrt(np.sum(np.abs(psi) ** 2))

    v = np.zeros(grid, dtype=np.float64)
    e = np.zeros((3,) + grid, dtype=np.float64)
    b = np.zeros((3,) + grid, dtype=np.float64)

    dt = 0.01
    n0 = float(np.sum(np.abs(psi) ** 2))
    for _ in range(20):
        psi = sim.propagate_wavefunction(psi, v, (e, b), dt)

    n1 = float(np.sum(np.abs(psi) ** 2))
    assert np.isfinite(n1)
    assert abs(n1 - n0) < 1e-10


def test_em_gauss_constraints_enforced_spectral():
    grid = (8, 8, 8)
    rng = np.random.default_rng(0)

    e0 = rng.standard_normal((3,) + grid).astype(np.float64)
    b0 = rng.standard_normal((3,) + grid).astype(np.float64)
    rho = rng.standard_normal(grid).astype(np.float64)
    rho_target = sim._project_rho_for_gauss(rho)
    j = np.zeros((3,) + grid, dtype=np.float64)

    e1, b1 = sim.update_em_fields(e0, b0, rho, j, dt=0.0)

    div_e = sim._divergence_spectral(e1)
    div_b = sim._divergence_spectral(b1)

    assert float(np.max(np.abs(div_e - rho_target))) < 1e-10
    assert float(np.max(np.abs(div_b))) < 1e-10
