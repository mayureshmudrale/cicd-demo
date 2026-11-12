import sys

from ai.llm import GeminiUnavailable
from ai.rca.analyze import analyze
from ai.rca.schemas import ErrorEvidence

# Keeping __init__.py empty (no `from .analyze import analyze` re-export)
# avoids the shadowing bug ai/routing/tests/test_decide.py had to work
# around, so a plain import is enough to get the real module here.
analyze_module = sys.modules["ai.rca.analyze"]

SAMPLE_EVIDENCE = [
    ErrorEvidence(
        trace_id="abc123",
        span_name="GET /ideas",
        http_route="/ideas",
        http_status_code=500,
        exception_type="RuntimeError",
        exception_message="simulated panic (FAULT_MODE=panic)",
        stacktrace_excerpt="...",
    )
]


def test_no_errors_in_window_short_circuits_without_gemini(monkeypatch):
    monkeypatch.setattr(analyze_module, "collect_error_evidence", lambda *a, **k: [])
    report = analyze("idea-board-backend", 0, 1)
    assert report.cited_trace_ids == []
    assert report.confidence == "high"


def test_gemini_unavailable_falls_back_to_citing_raw_evidence(monkeypatch):
    monkeypatch.setattr(analyze_module, "collect_error_evidence", lambda *a, **k: SAMPLE_EVIDENCE)

    def raise_unavailable(**kwargs):
        raise GeminiUnavailable("no cassette for this prompt")

    monkeypatch.setattr(analyze_module, "generate", raise_unavailable)

    report = analyze("idea-board-backend", 0, 1)
    assert report.cited_trace_ids == ["abc123"]
    assert report.confidence == "low"
