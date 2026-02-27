"""Integration tests — verify DI wiring returns the correct concrete type.

These tests complement test_di_wiring.py by going one step further:
they call get_client() and verify the returned instance is the expected
concrete type with the expected interface methods.  No real API calls
are made; environment variables are stubbed with fake values.
"""

from collections.abc import Generator
from unittest.mock import patch

import issue_tracker_client_api.client as _api
import pytest
from issue_tracker_client_api.client import IssueTrackerClient
from issue_tracker_client_impl.client import DefaultIssueTrackerClient


@pytest.fixture(autouse=True)
def _isolate_registry() -> Generator[None, None, None]:
    """Save and restore the global DI registry around each test."""
    saved = list(_api._factories)
    yield
    _api._factories.clear()
    _api._factories.extend(saved)


_FAKE_ENV = {"TRELLO_API_KEY": "fake-key", "TRELLO_API_TOKEN": "fake-token"}


def test_get_client_returns_concrete_type() -> None:
    """get_client() returns a DefaultIssueTrackerClient instance."""
    with patch.dict("os.environ", _FAKE_ENV):
        client = _api.get_client()
    assert isinstance(client, DefaultIssueTrackerClient)


def test_get_client_is_subclass_of_interface() -> None:
    """The object returned by get_client() satisfies the abstract contract."""
    with patch.dict("os.environ", _FAKE_ENV):
        client = _api.get_client()
    assert isinstance(client, IssueTrackerClient)


def test_concrete_client_exposes_interface_methods() -> None:
    """The concrete client has every method declared in the ABC."""
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
