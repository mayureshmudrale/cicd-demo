"""Combines the deterministic analyzers' findings into one verdict.

The pass/requires_approval verdict is computed deterministically from
finding severity alone — Gemini never sees or influences it. Its only job
is turning the structured findings into a human-readable summary and,
when approval is required, a concrete zero-downtime remediation plan.
GeminiUnavailable never blocks the verdict — it only means the summary/
plan fall back to the raw findings instead of prose.
"""

from pydantic import BaseModel

from ai.llm import GeminiUnavailable, generate

from .schemas import Finding, GatekeeperReport

APPROVAL_SEVERITIES = {"high", "critical"}

PROMPT_TEMPLATE = """You are a principal infrastructure architect reviewing
a pull request's blast radius before it merges. Here are the concrete,
already-verified findings (not your own analysis — summarize and act on
them, don't second-guess whether they're real):

{findings}

The merge gate's verdict is already decided deterministically: {verdict}.

Reply with strict JSON: {{"summary": "<1-3 sentences explaining the overall risk to a reviewer>", "remediation_plan": "<a concrete zero-downtime staged plan if verdict is requires_approval, else null>"}}
"""


class _GeminiSummary(BaseModel):
    """Response shape for the Gemini call — kept separate from
    GatekeeperReport since the verdict field must never come from the model."""

    summary: str
    remediation_plan: str | None = None


def _format_findings(findings: list[Finding]) -> str:
    return "\n".join(
        f"- [{f.severity}] ({f.source}) {f.location}: {f.reason}" for f in findings
    )


def _fallback_summary(findings: list[Finding], verdict: str) -> tuple[str, str | None]:
    """Only called with a non-empty `findings` — `gate()` short-circuits
    the empty case before ever reaching Gemini."""
    headline = f"{len(findings)} finding(s); highest severities: "
    headline += ", ".join(sorted({f.severity for f in findings}, reverse=True))
    plan = (
        "Gemini unavailable — review the findings above manually."
        if verdict == "requires_approval"
        else None
    )
    return headline, plan


def gate(findings: list[Finding]) -> GatekeeperReport:
    """Returns the full report for a set of findings from any mix of the
    terraform_risk / migration_risk / api_contract analyzers."""
    verdict = (
        "requires_approval"
        if any(f.severity in APPROVAL_SEVERITIES for f in findings)
        else "pass"
    )

    if not findings:
        return GatekeeperReport(
            verdict=verdict,
            findings=findings,
            summary="no risk findings in this change",
        )

    prompt = PROMPT_TEMPLATE.format(
        findings=_format_findings(findings), verdict=verdict
    )
    try:
        result = generate(
            feature="gatekeeper", prompt=prompt, response_schema=_GeminiSummary
        )
        summary, remediation_plan = result.summary, result.remediation_plan
    except GeminiUnavailable:
        summary, remediation_plan = _fallback_summary(findings, verdict)

    return GatekeeperReport(
        verdict=verdict,
        findings=findings,
        summary=summary,
        remediation_plan=remediation_plan,
    )
