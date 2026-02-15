"""Tests for issue_tracker_client_api data models and DI mechanism."""

import dataclasses

import issue_tracker_client_api.client as _reg
import pytest
from issue_tracker_client_api.client import (
    Comment,
    Issue,
    IssueTrackerClient,
    get_client,
    register,
)

_COMMENT_ID = 42


class _MockClient(IssueTrackerClient):
    def list_issues(self, _repo: str) -> list[Issue]:
        return []

    def get_issue(self, _repo: str, _issue_id: int) -> Issue:
        raise NotImplementedError

    def create_issue(self, _repo: str, _title: str, _body: str) -> Issue:
        raise NotImplementedError

    def close_issue(self, _repo: str, _issue_id: int) -> None:
        raise NotImplementedError

    def add_comment(self, _repo: str, _issue_id: int, _body: str) -> Comment:
        raise NotImplementedError


def test_issue_dataclass() -> None:
    """Issue is a frozen dataclass with the expected fields."""
    issue = Issue(id=1, title="Bug", body="Details here.", state="open")
    assert issue.id == 1
    assert issue.title == "Bug"
    assert issue.state == "open"


def test_issue_is_frozen() -> None:
    """Issue raises FrozenInstanceError on mutation attempt."""
    issue = Issue(id=1, title="Bug", body="Details here.", state="open")
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.id = 99  # type: ignore[misc]


def test_comment_dataclass() -> None:
    """Comment is a frozen dataclass with the expected fields."""
    comment = Comment(id=_COMMENT_ID, body="looks good")
    assert comment.id == _COMMENT_ID
    assert comment.body == "looks good"


def test_get_client_raises_without_factory() -> None:
    """get_client raises RuntimeError when no factory is registered."""
    saved = list(_reg._factories)
    _reg._factories.clear()
    try:
        with pytest.raises(RuntimeError):
            get_client()
    finally:
        _reg._factories.clear()
        _reg._factories.extend(saved)


def test_register_and_get_client() -> None:
    """Registered factory is used by get_client."""
    register(_MockClient)
    client = get_client()
    assert isinstance(client, _MockClient)
    assert client.list_issues("owner/repo") == []
