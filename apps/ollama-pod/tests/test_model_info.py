import httpx
import pytest

from ollama_pod.model_info import (
    VRAM_OVERHEAD_FACTOR,
    get_model_size_gb,
    parse_model,
)


def test_parse_model_with_tag() -> None:
    assert parse_model("qwen2.5:7b") == ("qwen2.5", "7b")


def test_parse_model_without_tag() -> None:
    assert parse_model("llama3") == ("llama3", "latest")


def _fake_request(url: str = "https://example.com") -> httpx.Request:
    return httpx.Request("GET", url)


def _fake_manifest(model_bytes: int) -> dict:
    return {
        "layers": [
            {
                "mediaType": "application/vnd.ollama.image.model",
                "size": model_bytes,
            },
            {
                "mediaType": "application/vnd.ollama.image.license",
                "size": 1000,
            },
        ]
    }


def test_get_model_size_gb(monkeypatch: pytest.MonkeyPatch) -> None:
    model_bytes = 4 * (1024**3)  # 4 GB

    def mock_get(url: str, **kwargs) -> httpx.Response:
        return httpx.Response(200, json=_fake_manifest(model_bytes), request=_fake_request(url))

    monkeypatch.setattr(httpx, "get", mock_get)
    size = get_model_size_gb("test:latest")
    assert abs(size - 4.0) < 0.01


def test_get_model_size_gb_404(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_get(url: str, **kwargs) -> httpx.Response:
        return httpx.Response(404, request=_fake_request(url))

    monkeypatch.setattr(httpx, "get", mock_get)
    with pytest.raises(SystemExit, match="not found"):
        get_model_size_gb("nonexistent:v1")


def test_get_model_size_gb_no_model_layers(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_get(url: str, **kwargs) -> httpx.Response:
        return httpx.Response(200, json={"layers": []}, request=_fake_request(url))

    monkeypatch.setattr(httpx, "get", mock_get)
    with pytest.raises(SystemExit, match="No model layers"):
        get_model_size_gb("empty:latest")
