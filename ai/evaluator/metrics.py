"""Queries otel-lgtm's Mimir (Prometheus-compatible) for a canary's live
error rate and latency percentiles, keyed by its rollouts-pod-template-hash
(app/backend/otel.py tags every request metric with that label).
"""
import math
import os

import httpx

MIMIR_URL = os.environ.get("MIMIR_URL", "http://otel-lgtm.platform.svc.cluster.local:9090")
METRICS_WINDOW = os.environ.get("METRICS_WINDOW", "1m")


def _query(promql: str) -> float:
    """One instant query against Mimir's Prometheus HTTP API. NaN (e.g. a
    histogram_quantile with no data yet) and "no series" both read as 0."""
    resp = httpx.get(f"{MIMIR_URL}/api/v1/query", params={"query": promql}, timeout=5.0)
    resp.raise_for_status()
    result = resp.json()["data"]["result"]
    if not result:
        return 0.0
    value = float(result[0]["value"][1])
    return 0.0 if math.isnan(value) else value


def canary_metrics(pod_template_hash: str) -> dict:
    """Returns {error_rate, p95_ms, p99_ms} for one pod track over the last
    METRICS_WINDOW. All-zero (not an error) just means no traffic yet to
    measure; the hard guard in ai/routing/decide.py treats that as healthy."""
    label = f'pod_template_hash="{pod_template_hash}"'
    total = _query(f"sum(increase(http_requests_total{{{label}}}[{METRICS_WINDOW}]))")
    errors = _query(
        f'sum(increase(http_requests_total{{{label},status_code=~"5.."}}[{METRICS_WINDOW}]))'
    )
    return {
        "error_rate": (errors / total) if total > 0 else 0.0,
        "p95_ms": _query(
            f"histogram_quantile(0.95, sum(rate(http_request_duration_milliseconds_bucket{{{label}}}"
            f"[{METRICS_WINDOW}])) by (le))"
        ),
        "p99_ms": _query(
            f"histogram_quantile(0.99, sum(rate(http_request_duration_milliseconds_bucket{{{label}}}"
            f"[{METRICS_WINDOW}])) by (le))"
        ),
    }
