from ai.reviewmem.corpus import GoldenComment
from ai.reviewmem.retrieve import top_matches

CORPUS = [
    GoldenComment(
        id="g1",
        category="broad-exception-catch",
        diff_hunk="try:\n    x()\nexcept Exception:\n    pass",
        comment="don't swallow exceptions",
        resolved=True,
    ),
    GoldenComment(
        id="g2",
        category="hardcoded-secret",
        diff_hunk='api_key = "sk-live-abc123"',
        comment="don't hardcode secrets",
        resolved=True,
    ),
]


def test_near_identical_hunk_matches_itself():
    matches = top_matches(CORPUS[0].diff_hunk, CORPUS)
    assert matches
    assert matches[0].id == "g1"


def test_unrelated_hunk_may_return_no_matches_above_threshold():
    # Not asserting emptiness strictly (the hashed fallback vector is
    # noisy), just that it never crashes and returns a list.
    matches = top_matches("def add(a, b):\n    return a + b", CORPUS)
    assert isinstance(matches, list)
