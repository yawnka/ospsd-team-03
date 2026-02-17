"""Unit tests for the DI mechanism in issue_tracker_client_api."""

from collections.abc import Generator

import issue_tracker_client_api.client as _reg
import pytest
from issue_tracker_client_api.client import (
    Comment,
    Issue,
    IssueTrackerClient,
    get_client,
    register,
)


class _MockClient(IssueTrackerClient):
    def list_issues(self, _board: str) -> list[Issue]:
        return []

    def get_issue(self, _board: str, _issue_id: int) -> Issue:
        raise NotImplementedError

    def create_issue(self, _board: str, _title: str, _body: str) -> Issue:
        raise NotImplementedError

    def close_issue(self, _board: str, _issue_id: int) -> None:
        raise NotImplementedError

    def add_comment(self, _board: str, _issue_id: int, _body: str) -> Comment:
        raise NotImplementedError


@pytest.fixture(autouse=True)
def _restore_factories() -> Generator[None, None, None]:
    """Snapshot and restore the DI registry around each unit test."""
    saved = list(_reg._factories)
    yield
    _reg._factories.clear()
    _reg._factories.extend(saved)


def test_get_client_raises_without_factory() -> None:
    """get_client() raises RuntimeError when no factory is registered."""
    _reg._factories.clear()
    with pytest.raises(RuntimeError):
        get_client()


def test_register_and_get_client() -> None:
    """register() + get_client() returns an instance of the registered class."""
    register(_MockClient)
    assert isinstance(get_client(), _MockClient)
