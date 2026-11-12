"""Adaptive canary routing: advance / hold / rollback per step.

Hard guards run before any Gemini call and can short-circuit it entirely:
error rate or p99 past a fixed threshold is an instant rollback, never put
to a vote. Gemini is only consulted when the hard guards are clean, and any
failure to get a verdict falls back to "advance" (the static steps keep
driving the rollout), never to a silent hang.
"""
from pydantic import BaseModel

from ai.llm import GeminiUnavailable, generate

from .schemas import RoutingDecision

HARD_ERROR_RATE = 0.05  # 5%
HARD_P99_MS = 2000

PROMPT_TEMPLATE = """You are deciding whether a canary deployment should
advance, hold, or roll back, based on these live metrics from the canary
pods (last 1m window):

error_rate: {error_rate}
p95_ms: {p95_ms}
p99_ms: {p99_ms}

Reply with strict JSON: {{"action": "advance"|"hold"|"rollback", "reasoning": "<one sentence>"}}
"""


class CanaryMetrics(BaseModel):
    error_rate: float
    p95_ms: float
    p99_ms: float


def decide(metrics: CanaryMetrics) -> RoutingDecision:
    """Returns the routing verdict for one canary analysis tick."""
    if metrics.error_rate > HARD_ERROR_RATE or metrics.p99_ms > HARD_P99_MS:
        return RoutingDecision(
            action="rollback",
            reasoning=f"hard guard: error_rate={metrics.error_rate} p99_ms={metrics.p99_ms}",
        )

    prompt = PROMPT_TEMPLATE.format(**metrics.model_dump())
    try:
        return generate(feature="routing", prompt=prompt, response_schema=RoutingDecision)
    except GeminiUnavailable as exc:
        return RoutingDecision(action="advance", reasoning=f"fallback (Gemini unavailable): {exc}")
