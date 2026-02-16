"""Integration test — DI wiring via import side-effect."""

from collections.abc import Generator

import issue_tracker_client_api.client as _api
import pytest

# Importing from issue_tracker_client_impl triggers its __init__.py,
# which calls _api.register(DefaultIssueTrackerClient) as a side-effect.
from issue_tracker_client_impl.client import DefaultIssueTrackerClient


@pytest.fixture(autouse=True)
def _registry_snapshot() -> Generator[None, None, None]:
    """Snapshot and restore the DI registry to prevent cross-test interference."""
    saved = list(_api._factories)
    yield
    _api._factories.clear()
    _api._factories.extend(saved)


def test_importing_impl_registers_factory() -> None:
    """Importing issue_tracker_client_impl registers DefaultIssueTrackerClient."""
    assert _api._factories[0] is DefaultIssueTrackerClient
