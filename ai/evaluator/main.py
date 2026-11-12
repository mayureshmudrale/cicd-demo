"""HTTP wrapper around ai.routing.decide for Argo Rollouts' AnalysisTemplate
web provider.

AI_MODE_ROUTING controls whether a verdict actually affects the rollout:
  shadow  (default) - always reports "advance" to Argo, but logs the real
                       verdict, so nothing can block or roll back yet.
  enforce            - reports the real verdict; Argo's successCondition /
                       failureCondition then actually gate the rollout.

The AnalysisTemplate (deploy/helm/idea-board/templates/analysistemplate-routing.yaml)
passes the canary's live pod-template-hash via args.latest-hash (Argo's
`valueFrom.podTemplateHashValue: Latest`); this service queries Mimir for
that track's real error rate / p95 / p99 (metrics.py) rather than trusting
a value Argo has no way to compute itself.
"""
import logging
import os

from fastapi import FastAPI
from pydantic import BaseModel

from ai.routing import CanaryMetrics, decide

from .metrics import canary_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-evaluator")

AI_MODE_ROUTING = os.environ.get("AI_MODE_ROUTING", "shadow")

app = FastAPI(title="AI Evaluator")


class RoutingRequest(BaseModel):
    """Body Argo's web provider posts; see analysistemplate-routing.yaml."""

    canary_hash: str
    stable_hash: str = ""


@app.get("/healthz")
def healthz() -> dict:
    """Liveness/readiness probe target."""
    return {"status": "ok", "mode": AI_MODE_ROUTING}


@app.post("/decide")
def decide_route(req: RoutingRequest) -> dict:
    """Called by Argo's AnalysisTemplate web provider once per analysis tick."""
    live_metrics = canary_metrics(req.canary_hash)
    verdict = decide(CanaryMetrics(**live_metrics))
    logger.info(
        "routing verdict: action=%s reasoning=%s mode=%s canary_hash=%s metrics=%s",
        verdict.action,
        verdict.reasoning,
        AI_MODE_ROUTING,
        req.canary_hash,
        live_metrics,
    )

    argo_action = "advance" if AI_MODE_ROUTING == "shadow" else verdict.action

    return {
        "action": argo_action,
        "shadow_verdict": verdict.action,
        "reasoning": verdict.reasoning,
        "mode": AI_MODE_ROUTING,
        "metrics": live_metrics,
    }
