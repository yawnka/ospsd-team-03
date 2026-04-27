# Observability & Telemetry

The deployed service emits traces and metrics via OpenTelemetry to Grafana Cloud.

Added in **HW3 (Second Submission)**.

## Architecture

```
FastAPI (Cloud Run)
  └─ OpenTelemetry SDK (auto-instrumentation)
       └─ OTLP HTTP exporter
            └─ Grafana Cloud
                 └─ Grafana Dashboard (3 panels)
```

## Instrumentation

`telemetry.py` configures OpenTelemetry when `OTEL_EXPORTER_OTLP_ENDPOINT` is set:

| Signal | Exporter | Details |
|--------|----------|---------|
| Traces | OTLP HTTP (`/v1/traces`) | `BatchSpanProcessor` |
| Metrics | OTLP HTTP (`/v1/metrics`) | `PeriodicExportingMetricReader`, 10s interval |
| FastAPI auto | `FastAPIInstrumentor` | `http.server.duration` histograms + per-status-code counters |

The 10-second export interval (vs. the default 60s) ensures metrics flush before Cloud Run scales the instance to zero.

**Local / test behavior**: when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset, `setup_telemetry()` is a no-op. No observability infrastructure is needed to run locally or in CI.

## Grafana Dashboard

The dashboard is committed at `infrastructure/grafana/dashboard.json` and can be imported directly into any Grafana instance.

### Panels

| Panel | Query | What it shows |
|-------|-------|---------------|
| **Request Latency** | `histogram_quantile` over `http_server_duration_milliseconds_bucket` | p50, p95, p99 latency |
| **Success Rate** | ratio of 2xx responses to total requests | % of requests that succeeded |
| **Failure Rate** | ratio of 4xx + 5xx responses to total requests | % of requests that errored |

Filter by `service_name="issue-tracker-service"`.

## Required Environment Variables

| Variable | Purpose |
|----------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Grafana Cloud OTLP endpoint (e.g. `https://otlp-gateway-prod-us-east-0.grafana.net/otlp`) |
| `OTEL_EXPORTER_OTLP_HEADERS` | Base64-encoded `Authorization: Basic ...` header |
| `OTEL_SERVICE_NAME` | Service name label in Grafana (e.g. `issue-tracker-service`) |

These are stored in GCP Secret Manager and injected at runtime — never committed to source control.

## Telemetry Unit Tests

`components/issue_tracker_client_service/tests/test_telemetry.py` verifies:

- `setup_telemetry()` is a no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset
- Provider and exporter are configured correctly when the endpoint is set
- OTLP header parsing handles trailing slashes and URL-encoded values
