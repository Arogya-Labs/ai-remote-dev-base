import runpod

from ollama_pod.config import runpod_api_key


def find_cheapest_gpu(min_vram_gb: float) -> tuple[str, float]:
    """Find the cheapest available GPU with at least `min_vram_gb` VRAM.

    Returns (gpu_type_id, cost_per_hr).
    """
    runpod.api_key = runpod_api_key()

    gpus = runpod.get_gpus()
    candidates = [g for g in gpus if g["memoryInGb"] >= min_vram_gb]

    if not candidates:
        raise SystemExit(
            f"No GPUs found with >= {min_vram_gb:.1f} GB VRAM. "
            "Try a smaller model or specify --gpu-type manually."
        )

    best: tuple[str, float] | None = None

    for gpu in candidates:
        detail = runpod.get_gpu(gpu["id"])

        lowest = detail.get("lowestPrice", {}) or {}
        price = lowest.get("uninterruptablePrice")

        if price is None:
            community = detail.get("communityPrice")
            secure = detail.get("securePrice")
            prices = [p for p in (community, secure) if p is not None]
            price = min(prices) if prices else None

        if price is None:
            continue

        available = detail.get("communityCloud") or detail.get("secureCloud")
        if not available:
            continue

        if best is None or price < best[1]:
            best = (gpu["id"], price)

    if best is None:
        raise SystemExit(
            f"No available GPUs with >= {min_vram_gb:.1f} GB VRAM. "
            "Try again later or specify --gpu-type manually."
        )

    return best
