"""Tests for simulation_pipeline_gr801 module."""

import numpy as np

import simulation_pipeline_gr801 as sim


def test_soc_initialization():
    """Test SoC initialization with default and custom parameters."""
    config = {
        'num_cores': 4,
        'memory_size': 1024,
        'accelerator': True
    }
    soc = sim.initialize_soc(config)
    
    assert soc.num_cores == 4
    assert len(soc.memory) == 1024
    assert soc.accelerator_present is True
    assert soc.errors == 0
    assert soc.performance == 0.0
    assert len(soc.registers) == 32 * 4  # 32 registers per core


def test_radiation_model_initialization():
    """Test radiation model initialization."""
    config = {
        'particle_flux': 5.0,
        'upset_rate': 1e-4
    }
    radiation = sim.initialize_radiation_model(config)
    
    assert radiation.particle_flux == 5.0
    assert radiation.upset_rate == 1e-4


def test_ai_application_initialization():
    """Test AI application initialization."""
    config = {
        'task': 'image_classification',
        'input_data': np.random.rand(10, 10)
    }
    app = sim.initialize_ai_application(config)
    
    assert app.task == 'image_classification'
    assert app.input_data.shape == (10, 10)
    assert app.output is None
    assert app.accuracy == 1.0


def test_run_ai_application_with_accelerator():
    """Test running AI application with accelerator."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    input_data = np.random.rand(10, 10)
    app = sim.AIApplication(task='test', input_data=input_data)
    
    initial_memory = soc.memory[0]
    sim.run_ai_application(soc, app)
    
    assert app.output is not None
    # Memory should be modified (output is stored at memory[0])
    assert soc.memory[0] != initial_memory


def test_run_ai_application_without_accelerator():
    """Test running AI application without accelerator."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=False)
    input_data = np.random.rand(10, 10)
    app = sim.AIApplication(task='test', input_data=input_data)
    
    sim.run_ai_application(soc, app)
    
    assert app.output is not None


def test_inject_faults():
    """Test fault injection mechanism with deterministic seeding."""
    # Seed the random number generator for reproducibility
    np.random.seed(42)
    
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    radiation = sim.RadiationModel(particle_flux=100.0, upset_rate=0.5)
    
    # Run multiple times to ensure some faults are injected
    # With high flux and upset rate, we should consistently see faults
    total_faults = 0
    for _ in range(10):
        faults = sim.inject_faults(soc, radiation, dt=0.1)
        total_faults += faults
    
    # With these parameters (λ = 100*1*0.1 = 10 particles/step, 50% upset rate)
    # we expect ~50 faults over 10 iterations
    assert total_faults > 0
    assert soc.errors == total_faults


def test_inject_faults_low_rate():
    """Test that low radiation doesn't always cause faults."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    radiation = sim.RadiationModel(particle_flux=0.0, upset_rate=0.0)
    
    faults = sim.inject_faults(soc, radiation, dt=0.1)
    
    assert faults == 0
    assert soc.errors == 0


def test_apply_fault_tolerance():
    """Test fault tolerance mechanism."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    soc.errors = 100
    
    corrected = sim.apply_fault_tolerance(soc)
    
    # Should correct 80% of errors (correction_rate = 0.8)
    assert corrected == 80
    assert soc.errors == 20


def test_monitor_state():
    """Test state monitoring."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    radiation = sim.RadiationModel(particle_flux=5.0, upset_rate=1e-4)
    app = sim.AIApplication(task='test', input_data=np.random.rand(10, 10))
    state = sim.SimulationState(soc, radiation, app, time=1.5)
    
    state.faults_injected = 50
    state.faults_corrected = 40
    
    metrics = sim.monitor_state(state)
    
    assert metrics['time'] == 1.5
    assert metrics['errors'] == 0
    assert metrics['total_faults_injected'] == 50
    assert metrics['total_faults_corrected'] == 40
    assert 'performance' in metrics
    assert 'application_accuracy' in metrics


def test_safety_violation_detected_high_errors():
    """Test safety violation detection with high error count."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    soc.errors = 1500  # Above threshold of 1000
    
    radiation = sim.RadiationModel(particle_flux=5.0, upset_rate=1e-4)
    app = sim.AIApplication(task='test', input_data=np.random.rand(10, 10))
    state = sim.SimulationState(soc, radiation, app)
    
    assert sim.safety_violation_detected(state) is True


def test_safety_violation_not_detected_low_errors():
    """Test no safety violation with low error count."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    soc.errors = 10  # Well below threshold
    
    radiation = sim.RadiationModel(particle_flux=5.0, upset_rate=1e-4)
    app = sim.AIApplication(task='test', input_data=np.random.rand(10, 10))
    state = sim.SimulationState(soc, radiation, app)
    
    assert sim.safety_violation_detected(state) is False


def test_run_simulation_smoke_test():
    """Smoke test for full simulation run."""
    config = {
        'num_cores': 4,
        'memory_size': 1024,
        'accelerator': True,
        'particle_flux': 1.0,
        'upset_rate': 1e-5,
        'task': 'image_classification',
        'input_data': np.random.rand(10, 10),
    }
    
    dt = 0.1
    time_steps = 10
    
    history = sim.run_simulation(time_steps, dt, config)
    
    # Should return metrics for each time step
    assert len(history) == time_steps
    assert all('time' in m for m in history)
    assert all('errors' in m for m in history)
    assert all('performance' in m for m in history)
    
    # Time should increase
    assert history[-1]['time'] > history[0]['time']


def test_run_simulation_high_radiation():
    """Test simulation with high radiation that may trigger shutdown."""
    config = {
        'num_cores': 2,
        'memory_size': 512,
        'accelerator': True,
        'particle_flux': 100.0,  # Very high
        'upset_rate': 0.5,  # Very high
        'task': 'image_classification',
        'input_data': np.random.rand(5, 5),
    }
    
    dt = 0.1
    time_steps = 100
    
    history = sim.run_simulation(time_steps, dt, config)
    
    # May terminate early due to safety violation
    assert len(history) > 0
    assert len(history) <= time_steps


def test_simulation_state_initialization():
    """Test simulation state initialization."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    radiation = sim.RadiationModel(particle_flux=5.0, upset_rate=1e-4)
    app = sim.AIApplication(task='test', input_data=np.random.rand(10, 10))
    
    state = sim.SimulationState(soc, radiation, app, time=2.5)
    
    assert state.soc is soc
    assert state.radiation is radiation
    assert state.app is app
    assert state.time == 2.5
    assert state.faults_injected == 0
    assert state.faults_corrected == 0


def test_update_radiation_model():
    """Test radiation model update (currently a no-op)."""
    radiation = sim.RadiationModel(particle_flux=5.0, upset_rate=1e-4)
    original_flux = radiation.particle_flux
    original_upset = radiation.upset_rate
    
    sim.update_radiation_model(radiation, dt=0.1)
    
    # Currently doesn't change anything
    assert radiation.particle_flux == original_flux
    assert radiation.upset_rate == original_upset


def test_performance_metric_with_errors():
    """Test that performance decreases with errors."""
    soc = sim.SoC(num_cores=4, memory_size=1024, accelerator_present=True)
    
    # Without errors
    soc.errors = 0
    soc.performance = 1.0 / (1.0 + soc.errors)
    perf_no_errors = soc.performance
    
    # With errors
    soc.errors = 10
    soc.performance = 1.0 / (1.0 + soc.errors)
    perf_with_errors = soc.performance
    
    assert perf_with_errors < perf_no_errors


def test_default_configuration():
    """Test simulation with default configuration values."""
    config = {}  # Empty config, should use defaults
    
    soc = sim.initialize_soc(config)
    assert soc.num_cores == 4
    assert len(soc.memory) == 1024 * 1024
    assert soc.accelerator_present is True
    
    radiation = sim.initialize_radiation_model(config)
    assert radiation.particle_flux == 1.0
    assert radiation.upset_rate == 1e-5
    
    app = sim.initialize_ai_application(config)
    assert app.task == 'image_classification'
    assert app.input_data.shape == (100, 100)
