import sys

from ai.llm import GeminiUnavailable
from ai.reviewmem.corpus import GoldenComment
from ai.reviewmem.review import review_hunk
from ai.reviewmem.schemas import _GeminiFinding, _ReviewResponse

review_module = sys.modules["ai.reviewmem.review"]

CORPUS = [
    GoldenComment(
        id="golden-001",
        category="broad-exception-catch",
        diff_hunk="try:\n    x()\nexcept Exception:\n    pass",
        comment="don't swallow exceptions silently",
        resolved=True,
    )
]


def test_clean_code_produces_no_findings(monkeypatch):
    monkeypatch.setattr(review_module, "generate", lambda **kwargs: _ReviewResponse(findings=[]))
    findings = review_hunk("app.py:@@", "def add(a, b):\n    return a + b", CORPUS)
    assert findings == []


def test_new_observation_has_no_grounding(monkeypatch):
    monkeypatch.setattr(
        review_module,
        "generate",
        lambda **kwargs: _ReviewResponse(
            findings=[
                _GeminiFinding(severity="high", category="sql-injection", comment="use parameterized queries")
            ]
        ),
    )
    findings = review_hunk("app.py:@@", "query = f'SELECT * FROM x WHERE y={user_input}'", CORPUS)
    assert len(findings) == 1
    assert findings[0].grounded_in is None


def test_gemini_unavailable_falls_back_to_strongest_historical_match(monkeypatch):
    def raise_unavailable(**kwargs):
        raise GeminiUnavailable("no cassette for this prompt")

    monkeypatch.setattr(review_module, "generate", raise_unavailable)
    findings = review_hunk("app.py:@@", "try:\n    x()\nexcept Exception:\n    pass", CORPUS)
    assert len(findings) == 1
    assert findings[0].grounded_in == "golden-001"


def test_gemini_unavailable_with_no_match_produces_nothing(monkeypatch):
    def raise_unavailable(**kwargs):
        raise GeminiUnavailable("no cassette for this prompt")

    monkeypatch.setattr(review_module, "generate", raise_unavailable)
    findings = review_hunk("app.py:@@", "def add(a, b):\n    return a + b", [])
    assert findings == []
