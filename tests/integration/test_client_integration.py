"""Integration tests for DI wiring across implementation and adapter layers."""

import importlib
import sys
from collections.abc import Generator
from unittest.mock import patch

import issue_tracker_client_api.client as _api
import pytest
from issue_tracker_client_adapter.adapter import ServiceClientAdapter
from issue_tracker_client_api.client import IssueTrackerClient
from issue_tracker_client_impl.client import DefaultIssueTrackerClient

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _isolate_registry() -> Generator[None, None, None]:
    """Save and restore the global DI registry around each test."""
    saved = list(_api._factories)
    yield
    _api._factories.clear()
    _api._factories.extend(saved)


_IMPL_ENV = {"TRELLO_API_KEY": "fake-key", "TRELLO_API_TOKEN": "fake-token"}
_ADAPTER_ENV = {"ISSUE_TRACKER_SERVICE_URL": "http://example.test"}


def _reimport_and_register(package_name: str) -> None:
    """Re-import *package_name* so its registration side effect runs again."""
    _api._factories.clear()
    sys.modules.pop(package_name, None)
    importlib.import_module(package_name)
    assert _api._factories


def test_importing_impl_registers_factory() -> None:
    """Importing issue_tracker_client_impl registers a working impl factory."""
    with patch.dict("os.environ", _IMPL_ENV, clear=False):
        _reimport_and_register("issue_tracker_client_impl")
        client = _api.get_client()

    assert callable(_api._factories[0])
    assert isinstance(client, DefaultIssueTrackerClient)


def test_importing_adapter_registers_factory() -> None:
    """Importing issue_tracker_client_adapter registers a working adapter factory."""
    with patch.dict("os.environ", _ADAPTER_ENV, clear=False):
        _reimport_and_register("issue_tracker_client_adapter")
        client = _api.get_client()

    assert callable(_api._factories[0])
    assert isinstance(client, ServiceClientAdapter)


def test_get_client_is_subclass_of_interface() -> None:
    """The impl client returned by get_client() satisfies the abstract contract."""
    with patch.dict("os.environ", _IMPL_ENV, clear=False):
        _reimport_and_register("issue_tracker_client_impl")
        client = _api.get_client()

    assert isinstance(client, IssueTrackerClient)


@pytest.mark.parametrize(
    ("package_name", "env"),
    [
        ("issue_tracker_client_impl", _IMPL_ENV),
        ("issue_tracker_client_adapter", _ADAPTER_ENV),
    ],
)
def test_registered_client_exposes_interface_methods(
    package_name: str,
    env: dict[str, str],
) -> None:
    """Both registered clients expose the methods declared in the current ABC."""
    with patch.dict("os.environ", env, clear=False):
        _reimport_and_register(package_name)
        client = _api.get_client()

    expected = (
        "get_issue",
        "get_board",
        "get_issues",
        "get_boards",
        "update_issue",
        "update_board",
        "delete_issue",
        "delete_board",
        "create_issue",
        "create_board",
    )
    for method in expected:
        assert callable(getattr(client, method))
