"""Unit tests for issue_tracker_client_service.telemetry."""

from unittest.mock import MagicMock, call, patch

import pytest
from fastapi import FastAPI
from issue_tracker_client_service.telemetry import _parse_headers, setup_telemetry

# ── _parse_headers ────────────────────────────────────────────────────────────


def test_parse_headers_empty_string() -> None:
    assert _parse_headers("") == {}


def test_parse_headers_single_pair() -> None:
    assert _parse_headers("Authorization=Bearer token") == {
        "Authorization": "Bearer token"
    }


def test_parse_headers_multiple_pairs() -> None:
    result = _parse_headers("X-Scope-OrgID=1,Authorization=Basic abc")
    assert result == {"X-Scope-OrgID": "1", "Authorization": "Basic abc"}


def test_parse_headers_value_with_equals() -> None:
    # base64-encoded values contain '='; only the first '=' should split
    result = _parse_headers("Authorization=Basic dXNlcjpwYXNz==")
    assert result == {"Authorization": "Basic dXNlcjpwYXNz=="}


def test_parse_headers_skips_items_without_equals() -> None:
    result = _parse_headers("valid=yes,no-equals,also=fine")
    assert result == {"valid": "yes", "also": "fine"}


def test_parse_headers_strips_whitespace() -> None:
    result = _parse_headers(" key = value ")
    assert result == {"key": "value"}


def test_parse_headers_url_decodes_values() -> None:
    result = _parse_headers("Authorization=Basic%20dXNlcjpwYXNz")
    assert result == {"Authorization": "Basic dXNlcjpwYXNz"}


# ── setup_telemetry ───────────────────────────────────────────────────────────


def test_setup_telemetry_noop_without_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    app = MagicMock(spec=FastAPI)

    with patch(
        "issue_tracker_client_service.telemetry.FastAPIInstrumentor"
    ) as mock_inst:
        setup_telemetry(app)
        mock_inst.instrument_app.assert_not_called()


def test_setup_telemetry_configures_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "test-service")
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_HEADERS", raising=False)
    app = MagicMock(spec=FastAPI)

    with (
        patch(
            "issue_tracker_client_service.telemetry.TracerProvider"
        ) as mock_tp_cls,
        patch(
            "issue_tracker_client_service.telemetry.MeterProvider"
        ) as mock_mp_cls,
        patch("issue_tracker_client_service.telemetry.trace") as mock_trace,
        patch("issue_tracker_client_service.telemetry.metrics") as mock_metrics,
        patch(
            "issue_tracker_client_service.telemetry.FastAPIInstrumentor"
        ) as mock_inst,
        patch(
            "issue_tracker_client_service.telemetry.OTLPSpanExporter"
        ) as mock_span_exp,
        patch(
            "issue_tracker_client_service.telemetry.OTLPMetricExporter"
        ) as mock_metric_exp,
        patch(
            "issue_tracker_client_service.telemetry.BatchSpanProcessor"
        ) as mock_bsp,
        patch(
            "issue_tracker_client_service.telemetry.PeriodicExportingMetricReader"
        ) as mock_reader,
        patch("issue_tracker_client_service.telemetry.Resource") as mock_resource,
    ):
        setup_telemetry(app)

        # Resource created with service name
        mock_resource.create.assert_called_once_with({"service.name": "test-service"})

        # Trace exporter uses /v1/traces path with empty headers
        mock_span_exp.assert_called_once_with(
            endpoint="http://localhost:4318/v1/traces", headers={}
        )
        mock_bsp.assert_called_once()
        mock_tp_cls.assert_called_once()
        mock_trace.set_tracer_provider.assert_called_once()

        # Metric exporter uses /v1/metrics path with empty headers
        mock_metric_exp.assert_called_once_with(
            endpoint="http://localhost:4318/v1/metrics", headers={}
        )
        mock_reader.assert_called_once()
        mock_mp_cls.assert_called_once()
        mock_metrics.set_meter_provider.assert_called_once()

        # FastAPI instrumented with both providers
        mock_inst.instrument_app.assert_called_once_with(
            app,
            tracer_provider=mock_tp_cls.return_value,
            meter_provider=mock_mp_cls.return_value,
        )


def test_setup_telemetry_passes_parsed_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel:4318")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", "Authorization=Bearer tok")

    app = MagicMock(spec=FastAPI)
    expected_headers = {"Authorization": "Bearer tok"}

    with (
        patch("issue_tracker_client_service.telemetry.TracerProvider"),
        patch("issue_tracker_client_service.telemetry.MeterProvider"),
        patch("issue_tracker_client_service.telemetry.trace"),
        patch("issue_tracker_client_service.telemetry.metrics"),
        patch("issue_tracker_client_service.telemetry.FastAPIInstrumentor"),
        patch(
            "issue_tracker_client_service.telemetry.OTLPSpanExporter"
        ) as mock_span_exp,
        patch(
            "issue_tracker_client_service.telemetry.OTLPMetricExporter"
        ) as mock_metric_exp,
        patch("issue_tracker_client_service.telemetry.BatchSpanProcessor"),
        patch("issue_tracker_client_service.telemetry.PeriodicExportingMetricReader"),
        patch("issue_tracker_client_service.telemetry.Resource"),
    ):
        setup_telemetry(app)

        assert mock_span_exp.call_args == call(
            endpoint="http://otel:4318/v1/traces", headers=expected_headers
        )
        assert mock_metric_exp.call_args == call(
            endpoint="http://otel:4318/v1/metrics", headers=expected_headers
        )


def test_setup_telemetry_strips_trailing_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Trailing slash on endpoint must not produce "//v1/traces"
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel:4318/")
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_HEADERS", raising=False)

    app = MagicMock(spec=FastAPI)

    with (
        patch("issue_tracker_client_service.telemetry.TracerProvider"),
        patch("issue_tracker_client_service.telemetry.MeterProvider"),
        patch("issue_tracker_client_service.telemetry.trace"),
        patch("issue_tracker_client_service.telemetry.metrics"),
        patch("issue_tracker_client_service.telemetry.FastAPIInstrumentor"),
        patch(
            "issue_tracker_client_service.telemetry.OTLPSpanExporter"
        ) as mock_span_exp,
        patch(
            "issue_tracker_client_service.telemetry.OTLPMetricExporter"
        ) as mock_metric_exp,
        patch("issue_tracker_client_service.telemetry.BatchSpanProcessor"),
        patch("issue_tracker_client_service.telemetry.PeriodicExportingMetricReader"),
        patch("issue_tracker_client_service.telemetry.Resource"),
    ):
        setup_telemetry(app)

        assert mock_span_exp.call_args == call(
            endpoint="http://otel:4318/v1/traces", headers={}
        )
        assert mock_metric_exp.call_args == call(
            endpoint="http://otel:4318/v1/metrics", headers={}
        )
