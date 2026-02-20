import time

import httpx
import pytest
import runpod
from runpod.error import QueryError

from ollama_pod.pod import (
    create_ollama_pod,
    get_endpoint,
    pull_model,
    resolve_volume_datacenter,
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
    assert captured["volume_mount_path"] == "/runpod-volume"
    assert "volume_in_gb" not in captured


def test_get_endpoint_tcp() -> None:
    """Prefers TCP port mapping when runtime has ip:port."""
    pod = {
        "id": "abc123",
        "runtime": {
            "ports": [
                {"privatePort": 11434, "publicPort": 30042, "ip": "194.68.1.1", "type": "tcp"},
            ]
        },
    }
    assert get_endpoint(pod) == "http://194.68.1.1:30042"


def test_get_endpoint_fallback() -> None:
    """Falls back to proxy URL when no TCP mapping."""
    pod = {"id": "abc123", "runtime": {"ports": []}}
    assert get_endpoint(pod) == "https://abc123-11434.proxy.runpod.net"


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


@pytest.mark.parametrize(
    ("cloud_type", "expected"),
    [
        ("ALL", "ALL"),
        ("COMMUNITY", "COMMUNITY"),
        ("SECURE", "SECURE"),
    ],
)
def test_create_ollama_pod_passes_cloud_type(
    monkeypatch: pytest.MonkeyPatch, cloud_type: str, expected: str
) -> None:
    captured: dict = {}

    def mock_create(**kwargs) -> dict:
        captured.update(kwargs)
        return {"id": "pod-ct"}

    monkeypatch.setattr(runpod, "create_pod", mock_create)
    create_ollama_pod("NVIDIA RTX A5000", cloud_type=cloud_type)

    assert captured["cloud_type"] == expected


def test_create_ollama_pod_defaults_to_all(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def mock_create(**kwargs) -> dict:
        captured.update(kwargs)
        return {"id": "pod-default"}

    monkeypatch.setattr(runpod, "create_pod", mock_create)
    create_ollama_pod("NVIDIA RTX A5000")

    assert captured["cloud_type"] == "ALL"


def test_create_ollama_pod_query_error_with_volume_gives_actionable_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When RunPod rejects a GPU+cloud_type+datacenter combo, the error should
    explain the likely cause and suggest alternatives."""

    def mock_create(**kwargs) -> dict:
        raise QueryError("No resources available")

    monkeypatch.setattr(runpod, "create_pod", mock_create)

    with pytest.raises(SystemExit, match="may not be available as secure cloud") as exc_info:
        create_ollama_pod(
            "NVIDIA RTX 2000 Ada",
            network_volume_id="vol-xyz",
            cloud_type="SECURE",
        )
    # Should mention the volume and suggest alternatives
    msg = str(exc_info.value)
    assert "vol-xyz" in msg
    assert "--cloud-type any" in msg


def test_create_ollama_pod_query_error_without_volume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without a volume constraint, the error should still be clear but not
    suggest datacenter-specific advice."""

    def mock_create(**kwargs) -> dict:
        raise QueryError("No resources available")

    monkeypatch.setattr(runpod, "create_pod", mock_create)

    with pytest.raises(SystemExit, match="RunPod rejected deployment"):
        create_ollama_pod("NVIDIA RTX A5000", cloud_type="SECURE")


def test_create_ollama_pod_query_error_cloud_type_all_no_datacenter_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cloud_type=ALL with a volume should not suggest datacenter mismatch."""

    def mock_create(**kwargs) -> dict:
        raise QueryError("No resources available")

    monkeypatch.setattr(runpod, "create_pod", mock_create)

    with pytest.raises(SystemExit, match="RunPod rejected deployment") as exc_info:
        create_ollama_pod(
            "NVIDIA RTX A5000",
            network_volume_id="vol-xyz",
            cloud_type="ALL",
        )
    assert "may not be available" not in str(exc_info.value)


def test_resolve_volume_datacenter_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runpod,
        "get_user",
        lambda: {
            "networkVolumes": [
                {"id": "vol-abc", "dataCenterId": "US-TX-3"},
                {"id": "vol-xyz", "dataCenterId": "EU-RO-1"},
            ]
        },
    )
    assert resolve_volume_datacenter("vol-xyz") == "EU-RO-1"


def test_resolve_volume_datacenter_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runpod,
        "get_user",
        lambda: {"networkVolumes": [{"id": "vol-abc", "dataCenterId": "US-TX-3"}]},
    )
    assert resolve_volume_datacenter("vol-unknown") is None
