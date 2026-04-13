"""OpenTelemetry instrumentation for the issue tracker service.

When ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set, this module configures:
- Tracing via OTLP HTTP exporter (spans per request)
- Metrics via OTLP HTTP exporter (latency, success/failure counts)
- FastAPI auto-instrumentation (``http.server.duration`` + request counts)

When the env var is absent, ``setup_telemetry`` is a no-op so the service
runs identically in local development without an observability backend.
"""

import os

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def _parse_headers(headers_str: str) -> dict[str, str]:
    """Parse ``key=value`` pairs from a comma-separated header string.

    Uses ``partition`` so values that contain ``=`` (e.g. base64 tokens) are
    preserved intact.
    """
    result: dict[str, str] = {}
    for item in headers_str.split(","):
        key, sep, value = item.partition("=")
        if sep:
            result[key.strip()] = value.strip()
    return result


def setup_telemetry(app: FastAPI) -> None:
    """Attach OTel tracing and metrics to *app*.

    No-op when ``OTEL_EXPORTER_OTLP_ENDPOINT`` is not set, so local
    development requires no observability infrastructure.
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return

    # Strip trailing slash so f"{endpoint}/v1/traces" never produces "//v1/traces".
    endpoint = endpoint.rstrip("/")

    service_name = os.getenv("OTEL_SERVICE_NAME", "issue-tracker-service")
    headers_raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    headers = _parse_headers(headers_raw) if headers_raw else {}

    resource = Resource.create({"service.name": service_name})

    # ── Tracing ───────────────────────────────────────────────────────────────
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", headers=headers)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # ── Metrics (latency / success rate / failure rate) ───────────────────────
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics", headers=headers)
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # FastAPI auto-instrumentation emits http.server.duration spans and the
    # per-status-code request counters that back success/failure rate panels.
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )
