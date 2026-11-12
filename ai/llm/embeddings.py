"""Shared Gemini embeddings client — same cassette-record/replay
discipline as client.py's generate(), but for embedding vectors used by
ai/reviewmem's retrieval step.

Unlike generate(), embedding failure never raises GeminiUnavailable: a
hashed bag-of-words vector is a real (if much lower-quality) stand-in for
a semantic embedding, so retrieval degrades to "worse recall," never to
"retrieval doesn't work at all."
"""

import hashlib
import json
import os
from pathlib import Path

from .cassette import CASSETTE_DIR
from .redact import redact

EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "text-embedding-004")
FALLBACK_DIM = 64


def _fallback_vector(text: str) -> list[float]:
    """Deterministic, offline hashed bag-of-words vector — not real
    semantics, but keeps cosine similarity meaningful enough that retrieval
    still functions without a live key."""
    vector = [0.0] * FALLBACK_DIM
    for word in text.lower().split():
        index = int(hashlib.sha256(word.encode()).hexdigest(), 16) % FALLBACK_DIM
        vector[index] += 1.0
    return vector


def _cassette_path(key: str) -> Path:
    return CASSETTE_DIR / "embeddings" / f"{key}.json"


def embed(text: str) -> list[float]:
    """Returns an embedding vector for `text` — from a recorded cassette,
    a live Gemini call (LIVE=1), or the deterministic fallback."""
    clean = redact(text)
    key = hashlib.sha256(f"{EMBED_MODEL}:{clean}".encode()).hexdigest()[:16]
    path = _cassette_path(key)

    if os.environ.get("LIVE") != "1":
        if path.exists():
            return json.loads(path.read_text())["embedding"]
        return _fallback_vector(clean)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _fallback_vector(clean)

    vector = _call_live(clean, api_key)
    if vector is None:
        return _fallback_vector(clean)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"text": clean, "embedding": vector}))
    return vector


def _call_live(text: str, api_key: str) -> list[float] | None:
    """None on any failure — embeddings always have a deterministic
    fallback, so there's nothing for the caller to catch."""
    from google import genai

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.embed_content(model=EMBED_MODEL, contents=text)
        return response.embeddings[0].values
    except Exception:  # noqa: BLE001 - any failure here just means "use the fallback"
        return None
