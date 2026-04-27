# Observability & Telemetry

The deployed services emit metrics via OpenTelemetry to Grafana Cloud.

Added in **HW3 (Second Submission)**.

## Architecture

```
FastAPI (Cloud Run)
  └─ OpenTelemetry SDK (auto-instrumentation)
       └─ OTLP HTTP exporter ─┐
                               ├─► Grafana Cloud
Discord Bot (GCE)              │     └─ Grafana Dashboard (7 panels)
  └─ OpenTelemetry SDK (manual)│
       └─ OTLP HTTP exporter ──┘
```

## Instrumentation

### Cloud Run service (`issue-tracker-service`)

`telemetry.py` configures OpenTelemetry when `OTEL_EXPORTER_OTLP_ENDPOINT` is set:

| Signal | Exporter | Details |
|--------|----------|---------|
| Traces | OTLP HTTP (`/v1/traces`) | `BatchSpanProcessor` |
| Metrics | OTLP HTTP (`/v1/metrics`) | `PeriodicExportingMetricReader`, 10s interval |
| FastAPI auto | `FastAPIInstrumentor` | `http.server.request.duration` histograms + per-status-code counters |

The 10-second export interval (vs. the default 60s) ensures metrics flush before Cloud Run scales the instance to zero.

`OTEL_SEMCONV_STABILITY_OPT_IN=http` is set in the Cloud Run environment to use the stable (NEW) HTTP semantic conventions (`http.server.request.duration` in seconds, `http.response.status_code` labels).

### Discord Bot (`discord-bot`)

`bot_telemetry.py` configures three custom metrics when `OTEL_EXPORTER_OTLP_ENDPOINT` is set:

| Metric | Type | Description |
|--------|------|-------------|
| `discord.bot.command.duration` | Histogram (unit: s) | AI command latency |
| `discord.bot.command.success` | Counter | Successful AI commands |
| `discord.bot.command.failure` | Counter | Failed AI commands |

**Local / test behavior**: when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset, both `setup_telemetry()` and `setup_bot_telemetry()` are no-ops. No observability infrastructure is needed to run locally or in CI.

## Grafana Dashboard

The dashboard is committed at `infrastructure/grafana/dashboard.json` (Grafana V2 / Dynamic Dashboards format) and can be imported via Grafana's "Edit as code" editor.

**Public dashboard**: <https://ospsd.grafana.net/public-dashboards/dc991557efdc4c608809a28ca4430b8c>

### Panels

**Cloud Run service** (`service_name="issue-tracker-service"`):

| Panel | Query | What it shows |
|-------|-------|---------------|
| **Request Latency** | `histogram_quantile` over `http_server_request_duration_seconds_bucket` | p50, p95, p99 latency |
| **Success Rate (2xx)** | ratio of 2xx responses to total requests | % of requests that succeeded |
| **Client Error Rate (4xx)** | ratio of 4xx responses to total requests | % of client errors |
| **Server Error Rate (5xx)** | ratio of 5xx responses to total requests | % of server errors |

**Discord Bot** (`service_name="discord-bot"`):

| Panel | Query | What it shows |
|-------|-------|---------------|
| **Command Latency** | `histogram_quantile` over `discord_bot_command_duration_seconds_bucket` | p50, p95, p99 latency |
| **Success Rate** | rate of `discord_bot_command_success_total` | Successful commands/s |
| **Failure Rate** | rate of `discord_bot_command_failure_total` | Failed commands/s |

## Required Environment Variables

| Variable | Purpose |
|----------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Grafana Cloud OTLP endpoint (e.g. `https://otlp-gateway-prod-us-east-0.grafana.net/otlp`) |
| `OTEL_EXPORTER_OTLP_HEADERS` | Base64-encoded `Authorization: Basic ...` header |
| `OTEL_SERVICE_NAME` | Service name label in Grafana (e.g. `issue-tracker-service` or `discord-bot`) |
| `OTEL_SEMCONV_STABILITY_OPT_IN` | Set to `http` on Cloud Run to use stable HTTP semantic conventions |

These are stored in GCP Secret Manager and injected at runtime — never committed to source control.

## Telemetry Unit Tests

`components/issue_tracker_client_service/tests/test_telemetry.py` verifies:

- `setup_telemetry()` is a no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` is unset
- Provider and exporter are configured correctly when the endpoint is set
- OTLP header parsing handles trailing slashes and URL-encoded values

`components/issue_tracker_client_service/tests/test_bot_telemetry.py` verifies:

- `setup_bot_telemetry()` returns no-op `BotMetrics` when endpoint is unset
- Meter provider and instruments are configured when endpoint is set
- `record_success()` / `record_failure()` are no-ops when disabled
