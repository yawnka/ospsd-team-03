"""Unit tests for the DI mechanism and public types in issue_tracker_client_api."""

import dataclasses
from collections.abc import Generator, Iterator

import issue_tracker_client_api.client as _reg
import pytest
from issue_tracker_client_api.client import (
    Board,
    BoardNotFoundError,
    Issue,
    IssueNotFoundError,
    IssueTrackerClient,
    Status,
    get_client,
    register,
)

pytestmark = pytest.mark.unit


class _MockClient(IssueTrackerClient):
    def get_boards(self) -> Iterator[Board]:
        return iter([])

    def get_board(self, _board_id: str) -> Board:
        raise NotImplementedError

    def get_issues(
        self, _board_id: str, _status: Status | None = None
    ) -> Iterator[Issue]:
        return iter([])

    def get_issue(self, _issue_id: str) -> Issue:
        raise NotImplementedError

    def create_issue(
        self,
        _title: str,
        _board_id: str,
        _desc: str | None = None,
        _members: list[str] | None = None,
        _due_date: str | None = None,
        _status: Status = Status.TO_DO,
    ) -> Issue:
        raise NotImplementedError

    def update_issue(
        self,
        _issue_id: str,
        _title: str | None = None,
        _desc: str | None = None,
        _members: list[str] | None = None,
        _due_date: str | None = None,
        _status: Status | None = None,
        _board_id: str | None = None,
    ) -> Issue:
        raise NotImplementedError

    def update_board(self, _board_id: str, _name: str | None = None) -> Board:
        raise NotImplementedError

    def delete_issue(self, _issue_id: str) -> bool:
        raise NotImplementedError

    def delete_board(self, _board_id: str) -> bool:
        raise NotImplementedError

    def create_board(self, _name: str) -> Board:
        raise NotImplementedError


@pytest.fixture(autouse=True)
def _restore_factories() -> Generator[None, None, None]:
    """Snapshot and restore the DI registry around each unit test."""
    saved = list(_reg._factories)
    yield
    _reg._factories.clear()
    _reg._factories.extend(saved)


# ---------------------------------------------------------------------------
# DI mechanism
# ---------------------------------------------------------------------------


def test_get_client_raises_without_factory() -> None:
    """get_client() raises RuntimeError when no factory is registered."""
    _reg._factories.clear()
    with pytest.raises(RuntimeError):
        get_client()


def test_register_and_get_client() -> None:
    """register() + get_client() returns an instance of the registered class."""
    register(_MockClient)
    assert isinstance(get_client(), _MockClient)


def test_register_replaces_previous_factory() -> None:
    """Calling register() twice keeps only the most recent factory."""

    class _OtherClient(_MockClient):
        pass

    register(_MockClient)
    register(_OtherClient)
    assert isinstance(get_client(), _OtherClient)


# ---------------------------------------------------------------------------
# Board dataclass
# ---------------------------------------------------------------------------


def test_board_has_id_and_name() -> None:
    """Board stores id and name and is immutable."""
    b = Board(id="abc123", name="Sprint Board")
    assert b.id == "abc123"
    assert b.name == "Sprint Board"


def test_board_is_frozen() -> None:
    """Board raises FrozenInstanceError when mutated."""
    b = Board(id="x", name="y")
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.id = "new"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Issue dataclass
# ---------------------------------------------------------------------------


def test_issue_has_expected_fields() -> None:
    """Issue stores id, board_id, title, desc, status, members, and due_date."""
    issue = Issue(
        id="card-id",
        board_id="board-id",
        title="Fix bug",
        desc="Detailed description",
        status=Status.TO_DO,
        members=["user1"],
        due_date="2026-05-01",
    )
    assert issue.id == "card-id"
    assert issue.board_id == "board-id"
    assert issue.title == "Fix bug"
    assert issue.desc == "Detailed description"
    assert issue.status == Status.TO_DO
    assert issue.members == ["user1"]
    assert issue.due_date == "2026-05-01"


def test_issue_optional_fields_default_to_none() -> None:
    """Issue.members and Issue.due_date default to None."""
    issue = Issue(id="c", board_id="b", title="t", desc="d", status=Status.IN_PROGRESS)
    assert issue.members is None
    assert issue.due_date is None


def test_issue_is_frozen() -> None:
    """Issue raises FrozenInstanceError when mutated."""
    issue = Issue(id="c", board_id="b", title="t", desc="d", status=Status.TO_DO)
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.title = "new"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


def test_issue_not_found_error_is_exception() -> None:
    """IssueNotFoundError is an Exception subclass."""
    err = IssueNotFoundError("card-id not found")
    assert isinstance(err, Exception)
    assert "card-id" in str(err)


def test_board_not_found_error_is_exception() -> None:
    """BoardNotFoundError is an Exception subclass."""
    err = BoardNotFoundError("board-id not found")
    assert isinstance(err, Exception)
    assert "board-id" in str(err)
