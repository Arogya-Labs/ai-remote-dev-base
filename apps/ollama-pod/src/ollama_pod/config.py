import os

from dotenv import load_dotenv

load_dotenv()


def _require(var: str) -> str:
    """Return the value of an environment variable or raise immediately."""
    value = os.environ.get(var)
    if not value:
        raise SystemExit(f"Missing required environment variable: {var}")
    return value


def runpod_api_key() -> str:
    return _require("RUNPOD_API_KEY")
