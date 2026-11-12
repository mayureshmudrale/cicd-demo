from ai.reviewmem.gate import select_findings
from ai.reviewmem.schemas import ReviewFinding


def _finding(severity):
    return ReviewFinding(location="x", severity=severity, category="c", comment="m")


def test_caps_to_max_comments():
    findings = [_finding("low")] * 10
    assert len(select_findings(findings, max_comments=3)) == 3


def test_orders_high_severity_first():
    findings = [_finding("low"), _finding("high"), _finding("medium")]
    selected = select_findings(findings, max_comments=3)
    assert [f.severity for f in selected] == ["high", "medium", "low"]
