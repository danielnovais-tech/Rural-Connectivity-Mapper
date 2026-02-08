# GR801 Simulation (Standalone)

This repo includes a lightweight simulation scaffold for a GR801 radiation-hardened AI SoC.

It is **standalone** and does **not** run the Rural Mapper data pipeline, does **not** touch `data/`, and does **not** require any external credentials.

## Run the demo

From the repo root (Windows PowerShell):

```powershell
.\.venv\Scripts\python.exe gr801_simulation_framework.py
```

This runs a short “radiation tolerance” sanity pass and then a mission simulation using the toy models.

## Use it from Python

```python
import numpy as np
import gr801_simulation_framework as gr

system = gr.GR801System(environment=gr.RadiationEnvironment.LEO)

# Advance simulation time (does not affect the Rural Mapper pipeline)
system.execute_timestep(dt=0.1)

model = gr.NeuralNetworkModel.get_preset_model(gr.AIWorkload.IMAGE_CLASSIFICATION)
input_data = np.random.standard_normal((1, *model.input_shape)).astype(np.float32)
result = system.run_inference(gr.AIWorkload.IMAGE_CLASSIFICATION, input_data)
print(result["estimated_accuracy"], result["result"].shape)
```

## Notes

- The “4GB DDR” is modeled as a sparse paged address space to avoid allocating multi‑GB arrays.
- CPU cycles and memory scrubbing are batched to keep the simulation fast in Python.
- This is a simulation scaffold, not a hardware-accurate model.
