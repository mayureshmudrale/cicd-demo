from typing import Literal

from pydantic import BaseModel


class ErrorEvidence(BaseModel):
    """One error span pulled straight from a real Tempo trace — never
    synthesized. See tempo.py."""

    trace_id: str
    span_name: str
    http_route: str | None = None
    http_status_code: int | None = None
    exception_type: str | None = None
    exception_message: str | None = None
    stacktrace_excerpt: str | None = None


class RCAReport(BaseModel):
    root_cause: str
    confidence: Literal["low", "medium", "high"]
    cited_trace_ids: list[str]
    suggested_fix: str
