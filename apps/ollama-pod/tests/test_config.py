import os

import pytest

from ollama_pod.config import _require


def test_require_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_VAR", "hello")
    assert _require("TEST_VAR") == "hello"


def test_require_raises_on_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(SystemExit, match="MISSING_VAR"):
        _require("MISSING_VAR")


def test_require_raises_on_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMPTY_VAR", "")
    with pytest.raises(SystemExit, match="EMPTY_VAR"):
        _require("EMPTY_VAR")
