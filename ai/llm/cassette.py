"""Record/replay for Gemini calls, keyed by input hash + prompt version.

Default mode replays a recorded cassette (deterministic, free, offline).
Set LIVE=1 to call Gemini for real and record a new cassette.
"""
import hashlib
import json
from pathlib import Path
from typing import Any

CASSETTE_DIR = Path(__file__).resolve().parents[1] / "evals" / "cassettes"


def cassette_key(*, feature: str, prompt: str, schema: str, prompt_version: str) -> str:
    digest = hashlib.sha256(f"{schema}:{prompt_version}:{prompt}".encode("utf-8")).hexdigest()
    return digest[:16]


def _path(feature: str, key: str) -> Path:
    return CASSETTE_DIR / feature / f"{key}.json"


def load_cassette(feature: str, key: str) -> dict[str, Any] | None:
    path = _path(feature, key)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def save_cassette(feature: str, key: str, *, request: str, response: dict[str, Any]) -> None:
    path = _path(feature, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"request": request, "response": response}, indent=2, sort_keys=True))
