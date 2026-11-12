"""OpenTelemetry wiring: traces go to otel-lgtm so RCA (feature #1) has
trace IDs and DB spans to cite; metrics go there too so feature #4
(adaptive canary routing) has real error-rate/latency data to query,
labeled by POD_TEMPLATE_HASH so the canary and stable tracks can be told
apart. Call `instrument(app, engine)` once at startup, after the FastAPI
app and SQLAlchemy engine both exist.
"""
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import settings

# Set via the Rollout's downward API (metadata.labels['rollouts-pod-template-hash']);
# "unknown" outside a Rollout-managed pod (e.g. `uvicorn main:app` locally).
POD_TEMPLATE_HASH = os.environ.get("POD_TEMPLATE_HASH", "unknown")

_request_counter = None
_duration_histogram = None


def instrument(app, engine) -> None:
    """Wire up OTLP trace+metric export and auto-instrument FastAPI + SQLAlchemy."""
    resource = Resource.create({SERVICE_NAME: settings.otel_service_name})

    otlp_endpoint = settings.otel_exporter_otlp_endpoint

    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(trace_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
        export_interval_millis=5000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    meter = metrics.get_meter("idea-board.backend")
    global _request_counter, _duration_histogram
    _request_counter = meter.create_counter(
        "http_requests_total",
        description="HTTP requests, labeled by status_code and pod_template_hash",
    )
    # Named without a unit suffix: the OTLP-to-Prometheus exporter appends
    # one derived from `unit=` itself (ms -> _milliseconds), so a name that
    # already said "ms" would render twice (http_request_duration_ms_milliseconds).
    _duration_histogram = meter.create_histogram(
        "http_request_duration",
        unit="ms",
        description="HTTP request duration, labeled by pod_template_hash",
    )

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)


def record_request(status_code: int, duration_ms: float) -> None:
    """Called once per request by the metrics middleware in main.py. Feeds
    the AI evaluator's canary-health query (ai/evaluator/metrics.py)."""
    attrs = {"status_code": str(status_code), "pod_template_hash": POD_TEMPLATE_HASH}
    _request_counter.add(1, attrs)
    _duration_histogram.record(duration_ms, attrs)
