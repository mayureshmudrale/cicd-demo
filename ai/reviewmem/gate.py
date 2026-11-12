"""Deterministic cap on what actually gets posted, regardless of how many
findings Gemini proposed across all of a PR's hunks."""

from .schemas import ReviewFinding

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def select_findings(
    findings: list[ReviewFinding], *, max_comments: int = 5
) -> list[ReviewFinding]:
    """Highest severity first, truncated to `max_comments` — never floods
    a PR no matter how many issues were proposed."""
    return sorted(findings, key=lambda finding: _SEVERITY_ORDER[finding.severity])[
        :max_comments
    ]
