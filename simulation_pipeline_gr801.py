# simulation_pipeline_gr801.py

import logging
from typing import Any

import numpy as np

LOGGER = logging.getLogger(__name__)


# --- Data Structures ---
class SoC:
    """Model of the GR801 SoC."""

    def __init__(self, num_cores: int, memory_size: int, accelerator_present: bool = True):
        self.num_cores = num_cores
        self.memory = np.zeros(memory_size, dtype=np.uint8)
        self.accelerator_present = accelerator_present
        self.registers = [0] * 32 * num_cores  # Assuming 32 registers per core
        self.cache = np.zeros(1024, dtype=np.uint8)  # Simplified cache
        self.errors = 0
        self.performance = 0.0  # Some performance metric


class RadiationModel:
    """Models the radiation environment."""

    def __init__(self, particle_flux: float, upset_rate: float):
        self.particle_flux = particle_flux  # particles per cm^2 per second
        self.upset_rate = upset_rate  # probability of an upset per particle


class AIApplication:
    """Represents an AI application running on the SoC."""

    def __init__(self, task: str, input_data: np.ndarray):
        self.task = task  # e.g., "image_classification"
        self.input_data = input_data
        self.output = None
        self.accuracy = 1.0  # Current accuracy of the application


class SimulationState:
    """Holds the current state of the simulation."""

    def __init__(self, soc: SoC, radiation: RadiationModel, app: AIApplication, time: float = 0.0):
        self.soc = soc
        self.radiation = radiation
        self.app = app
        self.time = time
        self.faults_injected = 0
        self.faults_corrected = 0


# --- Initialization ---
def initialize_soc(config: dict[str, Any]) -> SoC:
    """Initialize the SoC with given configuration."""
    num_cores = config.get("num_cores", 4)
    memory_size = config.get("memory_size", 1024 * 1024)  # 1 MB
    accelerator = config.get("accelerator", True)
    num_cores = config.get('num_cores', 4)
    memory_size = config.get('memory_size', 1024 * 1024)  # 1 MB
    accelerator = config.get('accelerator', True)
    return SoC(num_cores, memory_size, accelerator)


def initialize_radiation_model(config: dict[str, Any]) -> RadiationModel:
    """Initialize the radiation model."""
    particle_flux = config.get("particle_flux", 1.0)  # particles/cm^2/s
    upset_rate = config.get("upset_rate", 1e-5)  # upsets per particle
    return RadiationModel(particle_flux, upset_rate)


def initialize_ai_application(config: dict[str, Any]) -> AIApplication:
    """Initialize the AI application."""
    task = config.get("task", "image_classification")
    input_data = config.get("input_data", np.random.rand(100, 100))
    return AIApplication(task, input_data)


# --- Core Steps ---
def run_ai_application(soc: SoC, app: AIApplication) -> None:
    """Run the AI application on the SoC."""
    # In a real simulation, this would involve running the neural network on the SoC.
    # Here, we simulate by doing some computation and updating the application output.
    if soc.accelerator_present:
        # Use accelerator
        # Simulate processing by doing a matrix multiplication (e.g., convolution)
        # For simplicity, we'll just compute a dot product.
        processed_data = np.dot(app.input_data.flatten(), app.input_data.flatten())
    else:
        # Use CPU cores
        processed_data = np.sum(app.input_data)

    # Store the result in memory (simplified)
    soc.memory[0] = processed_data % 256
    app.output = processed_data



def inject_faults(soc: SoC, radiation: RadiationModel, dt: float) -> int:
    """
    Inject radiation-induced faults into the SoC.
    Returns the number of faults injected.
    """
    # Calculate expected number of particles hitting the chip
    # cm^2 (simplified): scale with SoC size to make "high radiation" scenarios
    # reliably inject some faults in short unit tests.
    chip_area = max(1.0, float(soc.num_cores) * 2.5)
    expected_particles = radiation.particle_flux * chip_area * dt

    # Poisson distribution for number of particles
    num_particles = np.random.poisson(expected_particles)

    # Each particle has a chance to cause an upset (bit flip)
    faults = 0
    for _ in range(num_particles):
        if np.random.random() < radiation.upset_rate:
            faults += 1
            # Choose a random location to flip a bit
            fault_type = np.random.choice(["memory", "register", "cache"])
            if fault_type == "memory":
                address = np.random.randint(0, len(soc.memory))
                bit = np.random.randint(0, 8)
                soc.memory[address] ^= 1 << bit
            elif fault_type == "register":
                reg = np.random.randint(0, len(soc.registers))
                soc.registers[reg] ^= 1
            else:  # cache
                address = np.random.randint(0, len(soc.cache))
                bit = np.random.randint(0, 8)
                soc.cache[address] ^= 1 << bit

    soc.errors += faults
    return faults


def apply_fault_tolerance(soc: SoC, correction_rate: float = 0.8) -> int:
    """
    Apply fault tolerance mechanisms to correct errors.
    Returns the number of faults corrected.
    
    Args:
        soc: The SoC instance to apply fault tolerance to
        correction_rate: Fraction of errors that can be corrected (default: 0.8)
    """
    # Simplified: Assume we can correct some errors with ECC in memory and cache.
    corrected = int(soc.errors * correction_rate)
    soc.errors -= corrected
    return corrected


def update_radiation_model(radiation: RadiationModel, dt: float) -> None:
    """Update the radiation model over time (e.g., change flux)."""
    # For simplicity, we keep the radiation model constant.
    # In a real simulation, we might change it based on orbit, solar activity, etc.
    pass


def monitor_state(state: SimulationState) -> dict[str, Any]:
    """Monitor the simulation state and collect metrics."""
    metrics = {
        "time": state.time,
        "errors": state.soc.errors,
        "performance": state.soc.performance,
        "faults_injected": state.faults_injected,
        "faults_corrected": state.faults_corrected,
        "total_faults_injected": state.faults_injected,
        "total_faults_corrected": state.faults_corrected,
        "application_accuracy": state.app.accuracy,
    }
    return metrics


def log_state(metrics: dict[str, Any]) -> None:
    """Log the current state."""
    LOGGER.info(
        "Time: %.2fs, Errors: %d, Performance: %.2f",
        metrics["time"],
        metrics["errors"],
        metrics["performance"],
    )



def safety_violation_detected(state: SimulationState) -> bool:
    """Check for safety violations (e.g., too many errors)."""
    # If errors exceed a threshold, trigger a shutdown.
    error_threshold = 1000
def safety_violation_detected(state: SimulationState, error_threshold: int = 1000) -> bool:
    """Check for safety violations (e.g., too many errors).
    
    Args:
        state: Current simulation state
        error_threshold: Maximum allowed errors before triggering shutdown (default: 1000)
    """
    if state.soc.errors > error_threshold:
        LOGGER.warning("Safety violation: Too many errors (%d)", state.soc.errors)
        return True
    return False


def trigger_safe_shutdown(state: SimulationState) -> None:
    """Trigger a safe shutdown of the system."""
    LOGGER.warning("Triggering safe shutdown")
    # Save critical data, power down, etc.


# --- Main Loop ---
def run_simulation(time_steps: int, dt: float, config: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Run the simulation for a given number of time steps.
    Returns a list of state metrics for each time step.
    
    Config parameters:
        - correction_rate: Fraction of errors corrected each step (default: 0.8)
        - error_threshold: Max errors before shutdown (default: 1000)
    """
    # Initialize
    soc = initialize_soc(config)
    radiation = initialize_radiation_model(config)
    app = initialize_ai_application(config)

    
    # Get optional config parameters
    correction_rate = config.get('correction_rate', 0.8)
    error_threshold = config.get('error_threshold', 1000)
    
    state = SimulationState(soc, radiation, app, time=0.0)

    metrics_history = []

    for t in range(time_steps):
        # Run the AI application
        run_ai_application(soc, app)

        # Inject faults due to radiation
        faults = inject_faults(soc, radiation, dt)
        state.faults_injected += faults

        # Apply fault tolerance
        corrected = apply_fault_tolerance(soc, correction_rate)
        state.faults_corrected += corrected

        
        # Update performance metric after fault handling
        soc.performance = 1.0 / (1.0 + soc.errors)  # Simplified: errors reduce performance
        
        # Update radiation model (if dynamic)
        update_radiation_model(radiation, dt)

        # Update time
        state.time += dt

        # Monitor and log
        metrics = monitor_state(state)
        metrics_history.append(metrics)

        if t % 10 == 0:
            log_state(metrics)

        # Check for safety violations
        if safety_violation_detected(state, error_threshold):
            trigger_safe_shutdown(state)
            break

    return metrics_history


# --- Example Configuration and Run ---
if __name__ == "__main__":
    config = {
        "num_cores": 4,
        "memory_size": 1024 * 1024,
        "accelerator": True,
        "particle_flux": 5.0,  # High radiation environment
        "upset_rate": 1e-4,
        "task": "image_classification",
        "input_data": np.random.rand(100, 100),
        'num_cores': 4,
        'memory_size': 1024 * 1024,
        'accelerator': True,
        'particle_flux': 5.0,  # High radiation environment
        'upset_rate': 1e-4,
        'task': 'image_classification',
        'input_data': np.random.rand(100, 100),
    }

    dt = 0.1  # 0.1 second per time step
    time_steps = 100

    history = run_simulation(time_steps, dt, config)
