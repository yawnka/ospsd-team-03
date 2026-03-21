"""Integration tests — verify DI wiring and client contract.

Tests that importing the implementation registers the factory,
that get_client() returns the correct concrete type, and that
the returned instance satisfies the abstract interface.
"""

import sys
from collections.abc import Generator
from unittest.mock import patch

import issue_tracker_client_api.client as _api
import pytest
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


_FAKE_ENV = {
    "TRELLO_API_KEY": "fake-key",
    "TRELLO_API_TOKEN": "fake-token",
    "ISSUE_TRACKER_SERVICE_URL": "http://localhost:8000",
}


def test_importing_impl_registers_factory() -> None:
    """Importing issue_tracker_client_impl registers a usable factory."""
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)
    import issue_tracker_client_impl  # noqa: PLC0415, F401

    assert _api._factories  # Ensure DI factory was registered before indexing
    factory = _api._factories[0]
    with patch.dict("os.environ", _FAKE_ENV):
        client = factory()

    assert isinstance(client, DefaultIssueTrackerClient)


def _register_impl_only() -> None:
    """Clear factories and register only the impl factory."""
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)
    import issue_tracker_client_impl  # noqa: PLC0415, F401


def test_get_client_returns_concrete_type() -> None:
    """get_client() returns a DefaultIssueTrackerClient instance."""
    _register_impl_only()
    with patch.dict("os.environ", _FAKE_ENV):
        client = _api.get_client()
    assert isinstance(client, DefaultIssueTrackerClient)


def test_get_client_is_subclass_of_interface() -> None:
    """The object returned by get_client() satisfies the abstract contract."""
    _register_impl_only()
    with patch.dict("os.environ", _FAKE_ENV):
        client = _api.get_client()
    assert isinstance(client, IssueTrackerClient)


def test_concrete_client_exposes_interface_methods() -> None:
    """The concrete client has every method declared in the ABC."""
    _register_impl_only()
    with patch.dict("os.environ", _FAKE_ENV):
        client = _api.get_client()
    expected = (
        "list_issues",
        "get_issue",
        "create_issue",
        "close_issue",
        "add_comment",
    )
    for method in expected:
        assert callable(getattr(client, method))
