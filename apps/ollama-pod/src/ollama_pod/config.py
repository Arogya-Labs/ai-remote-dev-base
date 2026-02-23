import os
from pathlib import Path

from dotenv import load_dotenv

# Load from ~/.ollama-pod/.env first, then fall back to cwd/.env
load_dotenv(Path.home() / ".ollama-pod" / ".env")
load_dotenv()  # cwd/.env — won't overwrite keys already set


def _require(var: str) -> str:
    """Return the value of an environment variable or raise immediately."""
    value = os.environ.get(var)
    if not value:
        raise SystemExit(f"Missing required environment variable: {var}")
    return value


def runpod_api_key() -> str:
    return _require("RUNPOD_API_KEY")
