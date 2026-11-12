"""Cosine-similarity retrieval of past review comments similar to a new
code hunk. Pure math, no AI judgment — the ranked result is CONTEXT fed
into review.py's actual review call, never a gate on whether a hunk gets
reviewed at all (every hunk gets reviewed regardless of retrieval hits).
"""

import math

from ai.llm.embeddings import embed

from .corpus import GoldenComment

# Loose on purpose: the fallback hashed-bag-of-words vectors (no live
# Gemini key) score real matches lower than true semantic embeddings
# would, so a strict threshold would silently drop them.
SIMILARITY_THRESHOLD = 0.2
TOP_K = 2

# Much stricter than SIMILARITY_THRESHOLD: used only by `confident_match`,
# where there's no later judgment call to reject a merely-plausible hit.
CONFIDENT_THRESHOLD = 0.6


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def scored_matches(
    hunk_text: str, corpus: list[GoldenComment]
) -> list[tuple[GoldenComment, float]]:
    """Every corpus entry paired with its similarity to `hunk_text`, above
    SIMILARITY_THRESHOLD, highest first."""
    hunk_vector = embed(hunk_text)
    scored = [(entry, _cosine(hunk_vector, embed(entry.diff_hunk))) for entry in corpus]
    above_threshold = [pair for pair in scored if pair[1] >= SIMILARITY_THRESHOLD]
    above_threshold.sort(key=lambda pair: pair[1], reverse=True)
    return above_threshold


def top_matches(hunk_text: str, corpus: list[GoldenComment]) -> list[GoldenComment]:
    """Up to TOP_K corpus entries most similar to `hunk_text` — used as
    CONTEXT for a live judgment call, which can and should disregard a
    weak one. See `confident_match` for the stricter bar needed when
    there's no judgment call to catch a bad match."""
    return [entry for entry, _ in scored_matches(hunk_text, corpus)[:TOP_K]]


def confident_match(
    hunk_text: str, corpus: list[GoldenComment]
) -> GoldenComment | None:
    """The single best match, but only if it clears a much stricter bar
    than `top_matches` — for the GeminiUnavailable fallback, which has no
    judgment step to reject a merely-plausible retrieval hit. Returning
    None (silence) is the safe default; a wrong citation is worse than no
    citation when nothing can double-check it."""
    scored = scored_matches(hunk_text, corpus)
    if not scored or scored[0][1] < CONFIDENT_THRESHOLD:
        return None
    return scored[0][0]
