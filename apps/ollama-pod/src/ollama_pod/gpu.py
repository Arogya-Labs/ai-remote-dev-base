from typing import Literal

import runpod

from ollama_pod.config import runpod_api_key

CloudType = Literal["any", "community", "secure"]


def _get_price_and_cloud(
    detail: dict, cloud_type: CloudType
) -> tuple[float, str] | None:
    """Extract (price, resolved_cloud_type) from a GPU detail dict, or None if unavailable."""
    if cloud_type == "community":
        if not detail.get("communityCloud"):
            return None
        price = detail.get("communityPrice")
        return (price, "community") if price else None

    if cloud_type == "secure":
        if not detail.get("secureCloud"):
            return None
        price = detail.get("securePrice")
        return (price, "secure") if price else None

    # cloud_type == "any": current behavior
    lowest = detail.get("lowestPrice", {}) or {}
    price = lowest.get("uninterruptablePrice") or None

    if price is None:
        community = detail.get("communityPrice")
        secure = detail.get("securePrice")
        prices = [p for p in (community, secure) if p]
        price = min(prices) if prices else None

    if price is None:
        return None

    available = detail.get("communityCloud") or detail.get("secureCloud")
    if not available:
        return None

    # Resolve which cloud type was chosen
    resolved = "community" if detail.get("communityCloud") else "secure"
    return (price, resolved)


def find_cheapest_gpu(
    min_vram_gb: float, cloud_type: CloudType = "any"
) -> tuple[str, float, str]:
    """Find the cheapest available GPU with at least `min_vram_gb` VRAM.

    Returns (gpu_type_id, cost_per_hr, cloud_type_used).
    """
    runpod.api_key = runpod_api_key()

    gpus = runpod.get_gpus()
    candidates = [g for g in gpus if g["memoryInGb"] >= min_vram_gb]

    if not candidates:
        raise SystemExit(
            f"No GPUs found with >= {min_vram_gb:.1f} GB VRAM. "
            "Try a smaller model or specify --gpu-type manually."
        )

    best: tuple[str, float, str] | None = None

    for gpu in candidates:
        detail = runpod.get_gpu(gpu["id"])
        result = _get_price_and_cloud(detail, cloud_type)
        if result is None:
            continue
        price, resolved = result

        if best is None or price < best[1]:
            best = (gpu["id"], price, resolved)

    if best is None:
        raise SystemExit(
            f"No available GPUs with >= {min_vram_gb:.1f} GB VRAM"
            f" (cloud_type={cloud_type!r}). "
            "Try again later or specify --gpu-type manually."
        )

    return best
