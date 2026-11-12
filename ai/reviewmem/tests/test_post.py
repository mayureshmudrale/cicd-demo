from ai.reviewmem.post import format_comment
from ai.reviewmem.schemas import ReviewFinding


def test_format_includes_severity_category_and_comment():
    findings = [
        ReviewFinding(location="a.py:@@", severity="high", category="sql-injection", comment="fix it"),
    ]
    body = format_comment(findings)
    assert "high" in body
    assert "sql-injection" in body
    assert "fix it" in body


def test_format_notes_grounding_when_present():
    findings = [
        ReviewFinding(
            location="a.py:@@", severity="high", category="x", comment="c", grounded_in="golden-001"
        )
    ]
    body = format_comment(findings)
    assert "golden-001" in body


def test_format_omits_grounding_note_when_absent():
    findings = [ReviewFinding(location="a.py:@@", severity="low", category="x", comment="c")]
    body = format_comment(findings)
    assert "grounded in" not in body


def test_format_always_includes_human_review_disclaimer():
    body = format_comment([ReviewFinding(location="a.py:@@", severity="low", category="x", comment="c")])
    assert "human review is still required" in body
