"""OpenTelemetry instrumentation for the Discord bot.

Emits the same three metric types as the Cloud Run service:
- Request latency (histogram)
- Success count (counter)
- Failure count (counter)

When ``OTEL_EXPORTER_OTLP_ENDPOINT`` is not set, all recording methods are
no-ops so the bot runs identically in local development.
"""

import os
from dataclasses import dataclass, field
from urllib.parse import unquote

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


def _parse_headers(headers_str: str) -> dict[str, str]:
    """Parse ``key=value`` pairs from a comma-separated header string."""
    result: dict[str, str] = {}
    for item in headers_str.split(","):
        key, sep, value = item.partition("=")
        if sep:
            result[unquote(key.strip())] = unquote(value.strip())
    return result


@dataclass
class BotMetrics:
    """Thin wrapper around OTel instruments for the Discord bot."""

    _enabled: bool = False
    _latency: metrics.Histogram = field(
        default_factory=lambda: metrics.NoOpHistogram("noop"),
    )
    _success: metrics.Counter = field(
        default_factory=lambda: metrics.NoOpCounter("noop"),
    )
    _failure: metrics.Counter = field(
        default_factory=lambda: metrics.NoOpCounter("noop"),
    )

    def record_success(self, duration_s: float) -> None:
        """Record a successful command execution."""
        if self._enabled:
            self._latency.record(duration_s, {"status": "success"})
            self._success.add(1)

    def record_failure(self, duration_s: float) -> None:
        """Record a failed command execution."""
        if self._enabled:
            self._latency.record(duration_s, {"status": "error"})
            self._failure.add(1)


def setup_bot_telemetry() -> BotMetrics:
    """Configure OTel metrics for the Discord bot and return a metrics handle.

    Returns a no-op ``BotMetrics`` when ``OTEL_EXPORTER_OTLP_ENDPOINT`` is unset.
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return BotMetrics()

    endpoint = endpoint.rstrip("/")
    service_name = os.getenv("OTEL_SERVICE_NAME", "discord-bot")
    headers_raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    headers = _parse_headers(headers_raw) if headers_raw else {}

    resource = Resource.create({"service.name": service_name})

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics", headers=headers),
        export_interval_millis=10_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    meter = meter_provider.get_meter("discord-bot")

    return BotMetrics(
        _enabled=True,
        _latency=meter.create_histogram(
            name="discord.bot.command.duration",
            description="AI command latency in seconds",
            unit="s",
        ),
        _success=meter.create_counter(
            name="discord.bot.command.success",
            description="Successful AI commands",
        ),
        _failure=meter.create_counter(
            name="discord.bot.command.failure",
            description="Failed AI commands",
        ),
    )
