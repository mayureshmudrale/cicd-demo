"""Root cause analysis (feature #1): pulls real error evidence (failing
routes, exception stacktraces) from Tempo for a service/time window and
asks Gemini for a root-cause hypothesis that must cite real trace IDs.

AI proposes, deterministic code disposes: if Gemini is unavailable, this
never invents a cause — it surfaces the raw evidence with low confidence
so a human can look at the cited trace IDs themselves.
"""
import textwrap

from ai.llm import GeminiUnavailable, generate

from .schemas import ErrorEvidence, RCAReport
from .tempo import collect_error_evidence

PROMPT_TEMPLATE = """You are performing root cause analysis for a web
backend from real distributed-tracing evidence below (each entry is one
error span from one real request trace, cited by its trace ID):

{evidence}

Return strict JSON: {{"root_cause": "<one or two sentences>", "confidence": "low"|"medium"|"high", "cited_trace_ids": [<trace IDs from the evidence above that support this>], "suggested_fix": "<one or two sentences>"}}

Only cite trace IDs that appear in the evidence above. If the evidence
doesn't clearly point to one cause, say so and use confidence "low".
"""


def _format_evidence(evidence: list[ErrorEvidence]) -> str:
    blocks = []
    for item in evidence:
        header = (
            f"- trace_id={item.trace_id} span={item.span_name} route={item.http_route} "
            f"status={item.http_status_code} exception={item.exception_type}: {item.exception_message}"
        )
        stacktrace = textwrap.indent(item.stacktrace_excerpt or "(no stacktrace captured)", "    ")
        blocks.append(f"{header}\n  stacktrace (last lines):\n{stacktrace}")
    return "\n".join(blocks)


def analyze(service_name: str, start: int, end: int, *, limit: int = 20) -> RCAReport:
    """Returns an RCA report for `service_name` over the unix-second
    window [start, end]."""
    evidence = collect_error_evidence(service_name, start, end, limit=limit)
    if not evidence:
        return RCAReport(
            root_cause="no error traces found in this window",
            confidence="high",
            cited_trace_ids=[],
            suggested_fix="none needed",
        )

    prompt = PROMPT_TEMPLATE.format(evidence=_format_evidence(evidence))
    try:
        return generate(feature="rca", prompt=prompt, response_schema=RCAReport)
    except GeminiUnavailable as exc:
        # A single error can mark more than one span in the same trace (e.g.
        # both the route handler's span and its "http send" child), so dedupe
        # while keeping first-seen order.
        unique_trace_ids = list(dict.fromkeys(item.trace_id for item in evidence))
        return RCAReport(
            root_cause=f"unknown (Gemini unavailable: {exc}); see cited evidence",
            confidence="low",
            cited_trace_ids=unique_trace_ids,
            suggested_fix="investigate manually using the cited trace IDs",
        )
