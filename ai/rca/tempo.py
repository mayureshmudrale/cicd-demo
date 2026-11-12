"""Pulls real error evidence (failing routes, exception stacktraces) from
Tempo for a service/time window, via Grafana's datasource proxy.

otel-lgtm provisions its Tempo datasource with a fixed uid ("tempo"), so
no discovery step is needed. Tempo's own TraceQL `{status=error}` filter
proved unreliable against this image (returned empty on known-error
windows); instead this fetches each candidate trace in full and checks
each span's own `status.code`, which is reliable.
"""
import os

import httpx

GRAFANA_URL = os.environ.get("GRAFANA_URL", "http://otel-lgtm.platform.svc.cluster.local:3000")
TEMPO_PROXY = f"{GRAFANA_URL}/api/datasources/proxy/uid/tempo"
STACKTRACE_EXCERPT_LINES = 6


def _attr(attributes: list[dict], key: str) -> str | None:
    for attribute in attributes:
        if attribute["key"] == key:
            return next(iter(attribute["value"].values()), None)
    return None


def search_candidates(service_name: str, start: int, end: int, limit: int) -> list[str]:
    """Trace IDs for the window; includes healthy traces too — callers
    filter for real errors via `errors_in_trace`."""
    resp = httpx.get(
        f"{TEMPO_PROXY}/api/search",
        params={"tags": f"service.name={service_name}", "start": start, "end": end, "limit": limit},
        timeout=10.0,
    )
    resp.raise_for_status()
    return [trace["traceID"] for trace in resp.json().get("traces", [])]


def get_trace(trace_id: str) -> dict:
    """Full OTLP-JSON trace detail (all batches/spans/events) for one trace ID."""
    resp = httpx.get(f"{TEMPO_PROXY}/api/traces/{trace_id}", timeout=10.0)
    resp.raise_for_status()
    return resp.json()


def _iter_spans(trace: dict):
    for batch in trace.get("batches", []):
        for scope_spans in batch.get("scopeSpans", []):
            yield from scope_spans.get("spans", [])


def _exception_from_events(span: dict) -> tuple[str | None, str | None, str | None]:
    """The OTel-recorded exception (type, message, last few stacktrace
    lines) for a span, if it has one — None, None, None otherwise."""
    for event in span.get("events") or []:
        if event.get("name") != "exception":
            continue
        event_attrs = event.get("attributes", [])
        exc_type = _attr(event_attrs, "exception.type")
        exc_message = _attr(event_attrs, "exception.message")
        full_trace = _attr(event_attrs, "exception.stacktrace") or ""
        excerpt = "\n".join(full_trace.splitlines()[-STACKTRACE_EXCERPT_LINES:])
        return exc_type, exc_message, excerpt
    return None, None, None


def errors_in_trace(trace: dict, trace_id: str) -> list["ErrorEvidence"]:
    """Every span Tempo itself marked STATUS_CODE_ERROR, with whatever
    exception event (if any) OTel attached to it."""
    from .schemas import ErrorEvidence

    found = []
    for span in _iter_spans(trace):
        if span.get("status", {}).get("code") != "STATUS_CODE_ERROR":
            continue
        attrs = span.get("attributes", [])
        exc_type, exc_message, stacktrace_excerpt = _exception_from_events(span)
        status_code = _attr(attrs, "http.status_code")
        found.append(
            ErrorEvidence(
                trace_id=trace_id,
                span_name=span.get("name", ""),
                http_route=_attr(attrs, "http.route"),
                http_status_code=int(status_code) if status_code else None,
                exception_type=exc_type,
                exception_message=exc_message,
                stacktrace_excerpt=stacktrace_excerpt,
            )
        )
    return found


def collect_error_evidence(service_name: str, start: int, end: int, *, limit: int = 20) -> list["ErrorEvidence"]:
    """Real evidence only, for the given unix-second window."""
    evidence = []
    for trace_id in search_candidates(service_name, start, end, limit):
        evidence.extend(errors_in_trace(get_trace(trace_id), trace_id))
    return evidence
