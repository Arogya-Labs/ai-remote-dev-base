import time

import httpx
import runpod
from runpod.error import QueryError

from ollama_pod.config import runpod_api_key

OLLAMA_IMAGE = "surajarogyalabs/kenai-ollama:latest"
OLLAMA_PORT = 11434
POLL_INTERVAL_S = 5

# Map CLI cloud_type values to RunPod mutation cloudType values
CLOUD_TYPE_MAP = {
    "any": "ALL",
    "community": "COMMUNITY",
    "secure": "SECURE",
}


def resolve_volume_datacenter(network_volume_id: str) -> str | None:
    """Look up the datacenter ID for a network volume. Returns None if not found."""
    runpod.api_key = runpod_api_key()
    user_info = runpod.get_user()
    for vol in user_info.get("networkVolumes", []):
        if vol["id"] == network_volume_id:
            return vol.get("dataCenterId")
    return None


def create_ollama_pod(
    gpu_type_id: str,
    *,
    name: str = "default",
    network_volume_id: str | None = None,
    cloud_type: str = "ALL",
    image: str | None = None,
) -> str:
    """Create a RunPod pod running Ollama. Returns the pod ID.

    cloud_type: "ALL", "COMMUNITY", or "SECURE" (RunPod mutation values).
    image: Docker image to use. Defaults to OLLAMA_IMAGE.

    Raises SystemExit with actionable message if RunPod rejects the
    GPU + cloud_type + datacenter combination.
    """
    runpod.api_key = runpod_api_key()

    kwargs: dict = {
        "name": f"ollama-{name}",
        "image_name": image or OLLAMA_IMAGE,
        "gpu_type_id": gpu_type_id,
        "cloud_type": cloud_type,
        "ports": f"{OLLAMA_PORT}/tcp",
        "container_disk_in_gb": 20,
    }

    if network_volume_id:
        kwargs["network_volume_id"] = network_volume_id
        kwargs["volume_mount_path"] = "/runpod-volume"
    else:
        kwargs["volume_in_gb"] = 50

    try:
        pod = runpod.create_pod(**kwargs)
    except QueryError as exc:
        msg = str(exc)
        # Provide actionable context when RunPod rejects the combination
        if network_volume_id and cloud_type != "ALL":
            raise SystemExit(
                f"RunPod rejected deployment: {msg}\n"
                f"  GPU {gpu_type_id} may not be available as "
                f"{cloud_type.lower()} cloud in the datacenter "
                f"pinned by volume {network_volume_id}.\n"
                f"  Try --cloud-type any, or pick a different --gpu-type."
            ) from exc
        raise SystemExit(f"RunPod rejected deployment: {msg}") from exc

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


def get_endpoint(pod: dict) -> str:
    """Return the best Ollama endpoint for a pod.

    Prefers the TCP port mapping (ip:port) when available, falls back
    to the RunPod HTTP proxy URL.
    """
    runtime = pod.get("runtime") or {}
    for port_info in runtime.get("ports") or []:
        if port_info.get("privatePort") == OLLAMA_PORT and port_info.get("ip"):
            ip = port_info["ip"]
            public_port = port_info["publicPort"]
            protocol = "https" if port_info.get("type") == "http" else "http"
            return f"{protocol}://{ip}:{public_port}"

    # Fallback: RunPod HTTP proxy
    pod_id = pod["id"]
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
