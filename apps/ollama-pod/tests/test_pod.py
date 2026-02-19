import time

import httpx
import pytest
import runpod

from ollama_pod.pod import (
    create_ollama_pod,
    get_endpoint,
    pull_model,
    terminate_pod,
    wait_for_ready,
)


@pytest.fixture(autouse=True)
def _mock_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNPOD_API_KEY", "test-key")


def test_create_ollama_pod_without_volume(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def mock_create(**kwargs) -> dict:
        captured.update(kwargs)
        return {"id": "pod-123"}

    monkeypatch.setattr(runpod, "create_pod", mock_create)
    pod_id = create_ollama_pod("NVIDIA RTX A5000")

    assert pod_id == "pod-123"
    assert captured["volume_in_gb"] == 50
    assert "network_volume_id" not in captured


def test_create_ollama_pod_with_volume(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def mock_create(**kwargs) -> dict:
        captured.update(kwargs)
        return {"id": "pod-456"}

    monkeypatch.setattr(runpod, "create_pod", mock_create)
    pod_id = create_ollama_pod("NVIDIA RTX A5000", network_volume_id="vol-abc")

    assert pod_id == "pod-456"
    assert captured["network_volume_id"] == "vol-abc"
    assert captured["volume_mount_path"] == "/root/.ollama"
    assert "volume_in_gb" not in captured


def test_get_endpoint() -> None:
    assert get_endpoint("abc123") == "https://abc123-11434.proxy.runpod.net"


def test_wait_for_ready_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    def mock_get_pod(pod_id: str) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            return {"id": pod_id, "runtime": {"ports": []}}
        return {"id": pod_id}

    monkeypatch.setattr(runpod, "get_pod", mock_get_pod)
    monkeypatch.setattr(time, "sleep", lambda _: None)

    pod = wait_for_ready("pod-123", timeout=30)
    assert pod["runtime"] is not None


def test_wait_for_ready_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runpod, "get_pod", lambda pod_id: {"id": pod_id})
    monkeypatch.setattr(time, "sleep", lambda _: None)

    # Use a very short timeout so monotonic check fails quickly
    start = time.monotonic()
    monkeypatch.setattr(
        time, "monotonic", lambda _start=start, _c=iter(range(1000)): _start + next(_c) * 100
    )

    with pytest.raises(SystemExit, match="did not become ready"):
        wait_for_ready("pod-123", timeout=1)


def test_pull_model(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def mock_post(url: str, **kwargs) -> httpx.Response:
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return httpx.Response(200, json={}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", mock_post)
    pull_model("https://pod-123-11434.proxy.runpod.net", "qwen2.5:7b")

    assert captured["url"] == "https://pod-123-11434.proxy.runpod.net/api/pull"
    assert captured["json"] == {"name": "qwen2.5:7b", "stream": False}


def test_terminate_pod(monkeypatch: pytest.MonkeyPatch) -> None:
    terminated: list[str] = []
    monkeypatch.setattr(runpod, "terminate_pod", lambda pod_id: terminated.append(pod_id))

    terminate_pod("pod-789")
    assert terminated == ["pod-789"]
