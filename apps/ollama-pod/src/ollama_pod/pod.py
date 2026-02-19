import time

import httpx
import runpod

from ollama_pod.config import runpod_api_key

OLLAMA_IMAGE = "ollama/ollama"
OLLAMA_PORT = 11434
POLL_INTERVAL_S = 5


def create_ollama_pod(
    gpu_type_id: str,
    network_volume_id: str | None = None,
) -> str:
    """Create a RunPod pod running Ollama. Returns the pod ID."""
    runpod.api_key = runpod_api_key()

    kwargs: dict = {
        "name": "ollama-pod",
        "image_name": OLLAMA_IMAGE,
        "gpu_type_id": gpu_type_id,
        "cloud_type": "ALL",
        "ports": f"{OLLAMA_PORT}/http",
        "container_disk_in_gb": 20,
        "env": {"OLLAMA_HOST": "0.0.0.0"},
    }

    if network_volume_id:
        kwargs["network_volume_id"] = network_volume_id
        kwargs["volume_mount_path"] = "/root/.ollama"
    else:
        kwargs["volume_in_gb"] = 50

    pod = runpod.create_pod(**kwargs)
    return pod["id"]


def wait_for_ready(pod_id: str, timeout: int = 300) -> dict:
    """Poll until the pod's runtime is populated. Returns pod info."""
    runpod.api_key = runpod_api_key()

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pod = runpod.get_pod(pod_id)
        if pod.get("runtime"):
            return pod
        time.sleep(POLL_INTERVAL_S)

    raise SystemExit(f"Pod {pod_id} did not become ready within {timeout}s")


def get_endpoint(pod_id: str) -> str:
    """Construct the Ollama HTTP endpoint URL for a RunPod pod."""
    return f"https://{pod_id}-{OLLAMA_PORT}.proxy.runpod.net"


def pull_model(endpoint: str, model: str, timeout: int = 600) -> None:
    """Pull a model on the remote Ollama instance."""
    url = f"{endpoint}/api/pull"
    resp = httpx.post(url, json={"name": model, "stream": False}, timeout=timeout)
    resp.raise_for_status()


def find_ollama_pods() -> list[dict]:
    """Return all RunPod pods that expose the Ollama port (11434)."""
    runpod.api_key = runpod_api_key()
    pods = runpod.get_pods()
    return [p for p in pods if str(OLLAMA_PORT) in (p.get("ports") or "")]


def terminate_pod(pod_id: str) -> None:
    """Terminate a RunPod pod."""
    runpod.api_key = runpod_api_key()
    runpod.terminate_pod(pod_id)
