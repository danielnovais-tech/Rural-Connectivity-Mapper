import numpy as np

import gr801_simulation_framework as gr


def test_memory_controller_sparse_does_not_allocate_full_space():
    mem = gr.MemoryController(size=gr.GR801Config.DDR4_ECC_SIZE)
    assert mem.size == gr.GR801Config.DDR4_ECC_SIZE
    assert mem.allocated_pages == 0

    payload = np.arange(256, dtype=np.uint8)
    mem.write(12345, payload)
    out = mem.read(12345, payload.size)

    assert np.array_equal(out, payload)
    assert mem.allocated_pages > 0


def test_system_inference_accepts_batched_inputs_and_returns_result():
    np.random.seed(0)

    system = gr.GR801System(environment=gr.RadiationEnvironment.LEO)
    model = gr.NeuralNetworkModel.get_preset_model(gr.AIWorkload.IMAGE_CLASSIFICATION)

    input_data = np.random.standard_normal((1, *model.input_shape)).astype(np.float32)
    result = system.run_inference(gr.AIWorkload.IMAGE_CLASSIFICATION, input_data)

    assert "result" in result
    assert "estimated_accuracy" in result

    y = result["result"]
    assert isinstance(y, np.ndarray)
    assert y.shape[0] == 1
