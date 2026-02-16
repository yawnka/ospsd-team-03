"""Integration test — DI wiring via import side-effect."""

import sys
from collections.abc import Generator

import issue_tracker_client_api.client as _api
import pytest
from issue_tracker_client_impl.client import DefaultIssueTrackerClient


@pytest.fixture(autouse=True)
def _isolate_registry() -> Generator[None, None, None]:
    """Clear DI registry before each test; restore original state after."""
    saved = list(_api._factories)
    _api._factories.clear()
    yield
    _api._factories.clear()
    _api._factories.extend(saved)


def test_importing_impl_registers_factory() -> None:
    """Importing issue_tracker_client_impl registers DefaultIssueTrackerClient."""
    assert not _api._factories                            # cleared by fixture
    sys.modules.pop("issue_tracker_client_impl", None)
    import issue_tracker_client_impl  # noqa: PLC0415, F401
    assert _api._factories[0] is DefaultIssueTrackerClient
