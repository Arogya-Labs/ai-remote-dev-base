import httpx

REGISTRY_BASE = "https://registry.ollama.ai/v2/library"
MODEL_MEDIA_TYPE = "application/vnd.ollama.image.model"
VRAM_OVERHEAD_FACTOR = 1.2


def parse_model(model: str) -> tuple[str, str]:
    """Split 'name:tag' into (name, tag). Defaults to 'latest'."""
    if ":" in model:
        name, tag = model.split(":", 1)
    else:
        name, tag = model, "latest"
    return name, tag


def get_model_size_gb(model: str) -> float:
    """Query the Ollama OCI registry for model weight size in GB."""
    name, tag = parse_model(model)
    url = f"{REGISTRY_BASE}/{name}/manifests/{tag}"

    resp = httpx.get(url, timeout=30)
    if resp.status_code == 404:
        raise SystemExit(f"Model not found: {model!r} (registry returned 404)")
    resp.raise_for_status()

    manifest = resp.json()
    total_bytes = sum(
        layer["size"]
        for layer in manifest.get("layers", [])
        if layer.get("mediaType") == MODEL_MEDIA_TYPE
    )
    if total_bytes == 0:
        raise SystemExit(f"No model layers found in manifest for {model!r}")

    return total_bytes / (1024**3)


def estimate_vram_gb(model: str) -> float:
    """Estimate VRAM needed: model size * overhead factor."""
    return get_model_size_gb(model) * VRAM_OVERHEAD_FACTOR
