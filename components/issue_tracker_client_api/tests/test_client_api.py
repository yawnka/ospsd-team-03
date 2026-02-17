"""Unit tests for the DI mechanism in issue_tracker_client_api."""

from collections.abc import Generator
from typing import Any

import issue_tracker_client_api.client as _reg
import pytest
from issue_tracker_client_api.client import (
    Comment,
    Issue,
    IssueTrackerClient,
    get_client,
    register,
)

pytestmark = pytest.mark.unit


class _MockClient(IssueTrackerClient):
    def list_issues(self, _board: str) -> list[Issue]:
        return []

    def get_issue(self, _board: str, _issue_id: int) -> Issue:
        raise NotImplementedError

    def create_issue(self, _board: str, _title: str, _body: str) -> Issue:
        raise NotImplementedError

    def close_issue(self, _board: str, _issue_id: int) -> bool:
        raise NotImplementedError

    def add_comment(self, _board: str, _issue_id: int, _body: str) -> Comment:
        raise NotImplementedError


@pytest.fixture(autouse=True)
def _restore_factory() -> Generator[None, None, None]:
    """Snapshot and restore the registered factory around each unit test.

    Note: we avoid touching private module state (e.g., _factories). Instead we
    snapshot the module-level get_client function state indirectly by grabbing
    the current factory (if any) and restoring when it teardowns.
    """
    prev_factory: Any | None
    try:
        prev_client = _reg.get_client()
        prev_factory = prev_client.__class__
    except RuntimeError:
        prev_factory = None

    yield

    if prev_factory is None:
        def _raise() -> IssueTrackerClient:
            msg = "No IssueTrackerClient factory has been registered."
            raise RuntimeError(msg)

        register(_raise)
    else:
        register(prev_factory)


def test_get_client_raises_without_factory() -> None:
    """get_client() raises RuntimeError when no factory is registered."""
    def _raise() -> IssueTrackerClient:
        msg = "No IssueTrackerClient factory has been registered."
        raise RuntimeError(msg)

    register(_raise)

    with pytest.raises(RuntimeError):
        get_client()


def test_register_and_get_client() -> None:
    """register() + get_client() returns an instance of the registered class."""
    register(_MockClient)
    assert isinstance(get_client(), _MockClient)
