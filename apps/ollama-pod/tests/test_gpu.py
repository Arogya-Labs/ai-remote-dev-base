import pytest
import runpod

from ollama_pod.gpu import find_cheapest_gpu

FAKE_GPUS = [
    {"id": "NVIDIA RTX A5000", "memoryInGb": 24},
    {"id": "NVIDIA RTX A6000", "memoryInGb": 48},
    {"id": "NVIDIA RTX 4090", "memoryInGb": 24},
]

FAKE_DETAILS = {
    "NVIDIA RTX A5000": {
        "lowestPrice": {"uninterruptablePrice": 0.20},
        "communityCloud": True,
        "secureCloud": True,
    },
    "NVIDIA RTX A6000": {
        "lowestPrice": {"uninterruptablePrice": 0.32},
        "communityCloud": True,
        "secureCloud": True,
    },
    "NVIDIA RTX 4090": {
        "lowestPrice": {"uninterruptablePrice": 0.34},
        "communityCloud": True,
        "secureCloud": False,
    },
}


@pytest.fixture(autouse=True)
def _mock_runpod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNPOD_API_KEY", "test-key")
    monkeypatch.setattr(runpod, "get_gpus", lambda: FAKE_GPUS)
    monkeypatch.setattr(runpod, "get_gpu", lambda gpu_id: FAKE_DETAILS[gpu_id])


def test_find_cheapest_gpu_picks_cheapest() -> None:
    gpu_id, price = find_cheapest_gpu(min_vram_gb=10.0)
    assert gpu_id == "NVIDIA RTX A5000"
    assert price == 0.20


def test_find_cheapest_gpu_respects_vram_filter() -> None:
    gpu_id, price = find_cheapest_gpu(min_vram_gb=30.0)
    assert gpu_id == "NVIDIA RTX A6000"
    assert price == 0.32


def test_find_cheapest_gpu_no_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runpod, "get_gpus", lambda: FAKE_GPUS)
    with pytest.raises(SystemExit, match="No GPUs found"):
        find_cheapest_gpu(min_vram_gb=100.0)


def test_find_cheapest_gpu_none_available(monkeypatch: pytest.MonkeyPatch) -> None:
    unavailable = {
        "NVIDIA RTX A5000": {
            "lowestPrice": {"uninterruptablePrice": 0.20},
            "communityCloud": False,
            "secureCloud": False,
        },
    }
    monkeypatch.setattr(runpod, "get_gpus", lambda: [FAKE_GPUS[0]])
    monkeypatch.setattr(runpod, "get_gpu", lambda gpu_id: unavailable[gpu_id])

    with pytest.raises(SystemExit, match="No available GPUs"):
        find_cheapest_gpu(min_vram_gb=10.0)
