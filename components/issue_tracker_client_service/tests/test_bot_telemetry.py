"""Tests for bot_telemetry module."""

from unittest.mock import patch

from issue_tracker_client_service.bot_telemetry import BotMetrics, setup_bot_telemetry


class TestBotMetrics:
    """Test BotMetrics recording methods."""

    def test_noop_when_disabled(self) -> None:
        """No-op metrics should not raise."""
        m = BotMetrics()
        m.record_success(0.5)
        m.record_failure(1.0)

    def test_record_success_when_enabled(self) -> None:
        """Enabled metrics should delegate to OTel instruments."""
        m = BotMetrics(_enabled=True)
        # NoOp instruments accept calls without error
        m.record_success(0.123)

    def test_record_failure_when_enabled(self) -> None:
        """Enabled metrics should delegate to OTel instruments."""
        m = BotMetrics(_enabled=True)
        m.record_failure(0.456)


class TestSetupBotTelemetry:
    """Test setup_bot_telemetry factory."""

    def test_returns_disabled_when_no_endpoint(self) -> None:
        """Without OTEL_EXPORTER_OTLP_ENDPOINT, returns disabled metrics."""
        with patch.dict("os.environ", {}, clear=True):
            metrics = setup_bot_telemetry()
        assert not metrics._enabled  # noqa: SLF001 — testing internal state

    def test_returns_enabled_when_endpoint_set(self) -> None:
        """With OTEL_EXPORTER_OTLP_ENDPOINT, returns enabled metrics."""
        env = {
            "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otlp.example.com",
            "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Basic dGVzdA==",
        }
        with patch.dict("os.environ", env, clear=True):
            metrics = setup_bot_telemetry()
        assert metrics._enabled  # noqa: SLF001 — testing internal state
