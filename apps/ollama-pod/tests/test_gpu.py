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
        "lowestPrice": {"uninterruptablePrice": 0.16},
        "communityPrice": 0.16,
        "securePrice": 0.27,
        "communityCloud": True,
        "secureCloud": True,
    },
    "NVIDIA RTX A6000": {
        "lowestPrice": {"uninterruptablePrice": 0.32},
        "communityPrice": 0.32,
        "securePrice": 0.44,
        "communityCloud": True,
        "secureCloud": True,
    },
    "NVIDIA RTX 4090": {
        "lowestPrice": {"uninterruptablePrice": 0.34},
        "communityPrice": 0.34,
        "securePrice": None,
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
    gpu_id, price, cloud = find_cheapest_gpu(min_vram_gb=10.0)
    assert gpu_id == "NVIDIA RTX A5000"
    assert price == 0.16
    assert cloud == "community"


def test_find_cheapest_gpu_respects_vram_filter() -> None:
    gpu_id, price, cloud = find_cheapest_gpu(min_vram_gb=30.0)
    assert gpu_id == "NVIDIA RTX A6000"
    assert price == 0.32
    assert cloud == "community"


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


def test_cloud_type_community_picks_community_price() -> None:
    gpu_id, price, cloud = find_cheapest_gpu(min_vram_gb=10.0, cloud_type="community")
    assert gpu_id == "NVIDIA RTX A5000"
    assert price == 0.16
    assert cloud == "community"


def test_cloud_type_secure_picks_secure_price() -> None:
    gpu_id, price, cloud = find_cheapest_gpu(min_vram_gb=10.0, cloud_type="secure")
    assert gpu_id == "NVIDIA RTX A5000"
    assert price == 0.27
    assert cloud == "secure"


def test_cloud_type_secure_skips_unavailable() -> None:
    """RTX 4090 has secureCloud=False, so it should be skipped for secure cloud."""
    gpu_id, price, cloud = find_cheapest_gpu(min_vram_gb=10.0, cloud_type="secure")
    # A5000 is cheapest secure at $0.27, 4090 has no secure cloud
    assert gpu_id == "NVIDIA RTX A5000"
    assert price == 0.27
    assert cloud == "secure"


def test_cloud_type_secure_none_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """All GPUs lack secure cloud — should raise."""
    no_secure = {
        "NVIDIA RTX A5000": {
            "communityPrice": 0.16,
            "securePrice": None,
            "communityCloud": True,
            "secureCloud": False,
        },
    }
    monkeypatch.setattr(runpod, "get_gpus", lambda: [FAKE_GPUS[0]])
    monkeypatch.setattr(runpod, "get_gpu", lambda gpu_id: no_secure[gpu_id])

    with pytest.raises(SystemExit, match="cloud_type='secure'"):
        find_cheapest_gpu(min_vram_gb=10.0, cloud_type="secure")


def test_cloud_type_any_is_default_behavior() -> None:
    """cloud_type='any' should use lowestPrice and pick the cheapest overall."""
    gpu_id, price, cloud = find_cheapest_gpu(min_vram_gb=10.0, cloud_type="any")
    assert gpu_id == "NVIDIA RTX A5000"
    assert price == 0.16
