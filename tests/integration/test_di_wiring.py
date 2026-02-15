"""Integration tests — DI wiring between api and impl packages."""

import issue_tracker_client_api.client as _api
import pytest

# Importing from impl triggers issue_tracker_client_impl/__init__.py,
# which registers DefaultIssueTrackerClient as the active factory.
from issue_tracker_client_impl.client import DefaultIssueTrackerClient


@pytest.fixture(autouse=True)
def _re_register() -> None:
    """Ensure DefaultIssueTrackerClient is registered before each test."""
    _api.register(DefaultIssueTrackerClient)


def test_import_impl_registers_factory() -> None:
    """Importing issue_tracker_client_impl registers DefaultIssueTrackerClient."""
    assert _api._factories[0] is DefaultIssueTrackerClient


def test_get_client_returns_default_impl(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_client() returns a DefaultIssueTrackerClient after impl is imported."""
    monkeypatch.setenv("ISSUE_TRACKER_TOKEN", "test-token")
    client = _api.get_client()
    assert isinstance(client, DefaultIssueTrackerClient)
