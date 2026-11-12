import sys

import pytest

from ai.llm import GeminiUnavailable
from ai.routing.decide import CanaryMetrics, decide

# ai/routing/__init__.py does `from .decide import decide`, which rebinds the
# `decide` attribute on the `ai.routing` package to the function, shadowing
# the submodule. Go through sys.modules to get the actual module to patch.
decide_module = sys.modules["ai.routing.decide"]


def test_hard_guard_rollback_on_high_error_rate():
    metrics = CanaryMetrics(error_rate=0.5, p95_ms=100, p99_ms=200)
    result = decide(metrics)
    assert result.action == "rollback"
    assert "hard guard" in result.reasoning


def test_hard_guard_rollback_on_high_p99():
    metrics = CanaryMetrics(error_rate=0.0, p95_ms=100, p99_ms=5000)
    result = decide(metrics)
    assert result.action == "rollback"
    assert "hard guard" in result.reasoning


def test_gemini_unavailable_falls_back_to_advance(monkeypatch: pytest.MonkeyPatch):
    def raise_unavailable(**kwargs):
        raise GeminiUnavailable("no cassette for this prompt")

    monkeypatch.setattr(decide_module, "generate", raise_unavailable)

    metrics = CanaryMetrics(error_rate=0.0, p95_ms=100, p99_ms=200)
    result = decide(metrics)
    assert result.action == "advance"
    assert "fallback" in result.reasoning
