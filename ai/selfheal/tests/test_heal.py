import sys

from ai.llm import GeminiUnavailable
from ai.selfheal.heal import propose_fix
from ai.selfheal.schemas import FileEdit, PatchProposal

heal_module = sys.modules["ai.selfheal.heal"]


def test_returns_proposal_from_generate(monkeypatch):
    expected = PatchProposal(
        explanation="remove unused import",
        edits=[FileEdit(path="a.py", new_content="x = 1\n")],
    )
    monkeypatch.setattr(heal_module, "generate", lambda **kwargs: expected)

    result = propose_fix("ruff check .", "a.py:1:1: F401 unused", {"a.py": "import os\nx = 1\n"})
    assert result == expected


def test_gemini_unavailable_returns_none(monkeypatch):
    def raise_unavailable(**kwargs):
        raise GeminiUnavailable("no cassette for this prompt")

    monkeypatch.setattr(heal_module, "generate", raise_unavailable)
    result = propose_fix("ruff check .", "some output", {"a.py": "content"})
    assert result is None
