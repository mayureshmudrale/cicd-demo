import sys

from ai.gatekeeper.gate import gate
from ai.gatekeeper.schemas import Finding
from ai.llm import GeminiUnavailable

gate_module = sys.modules["ai.gatekeeper.gate"]

HIGH_FINDING = Finding(source="terraform", location="x", severity="high", reason="destructive")
LOW_FINDING = Finding(source="migration", location="y", severity="low", reason="minor")


def test_no_findings_passes_without_calling_gemini(monkeypatch):
    def fail(**kwargs):
        raise AssertionError("gate() must not call Gemini with no findings")

    monkeypatch.setattr(gate_module, "generate", fail)
    report = gate([])
    assert report.verdict == "pass"


def test_low_severity_only_passes():
    report = gate([LOW_FINDING])
    assert report.verdict == "pass"


def test_high_severity_requires_approval():
    report = gate([HIGH_FINDING, LOW_FINDING])
    assert report.verdict == "requires_approval"


def test_verdict_survives_gemini_unavailable(monkeypatch):
    def raise_unavailable(**kwargs):
        raise GeminiUnavailable("no cassette for this prompt")

    monkeypatch.setattr(gate_module, "generate", raise_unavailable)
    report = gate([HIGH_FINDING])
    assert report.verdict == "requires_approval"
    assert report.remediation_plan is not None
