"""Loads the golden/seed corpus of past human review comments.

This repo has no real PR history to mine yet, so `data/golden_comments.json`
is a hand-written seed grounded in this codebase's own actually-enforced
review standards (GeminiUnavailable fallbacks, no hardcoded secrets, no
broad exception swallowing, ...) rather than fabricated examples. See
ai/gatekeeper's README section on real GitHub-API retrieval for how this
would be replaced with a real mined corpus.
"""

import json
from pathlib import Path

from pydantic import BaseModel

DATA_PATH = Path(__file__).parent / "data" / "golden_comments.json"


class GoldenComment(BaseModel):
    id: str
    category: str
    diff_hunk: str
    comment: str
    resolved: bool


def load_corpus() -> list[GoldenComment]:
    """Returns every entry in the golden/seed corpus."""
    entries = json.loads(DATA_PATH.read_text())
    return [GoldenComment(**entry) for entry in entries]
