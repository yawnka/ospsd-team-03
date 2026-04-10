"""Tests for the shared-contract ServiceClientAdapter."""

import importlib
from unittest.mock import MagicMock, patch

import pytest
from issue_tracker_client_adapter.adapter import ServiceClientAdapter
from issue_tracker_client_api.client import (
    Board,
    BoardNotFoundError,
    Issue,
    IssueCreateError,
    IssueNotFoundError,
    Status,
    get_client,
)
from issue_tracker_client_service_client.models import BoardOut, IssueOut, SuccessOut

from issue_tracker_client_service_client import errors

pytestmark = pytest.mark.unit


@pytest.fixture
def adapter() -> ServiceClientAdapter:
    """Return a ServiceClientAdapter instance."""
    return ServiceClientAdapter(base_url="http://localhost:8000")


def _issue_out(
    *,
    issue_id: str = "issue-1",
    board_id: str = "board-1",
    title: str = "Test Issue",
    desc: str = "Test Desc",
    status: str = "to_do",
) -> IssueOut:
    """Create a wire-format IssueOut fixture."""
    return IssueOut(
        id=issue_id,
        title=title,
        desc=desc,
        members=None,
        due_date=None,
        status=status,
        board_id=board_id,
    )


def test_import_registers_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Importing the adapter package registers ServiceClientAdapter as the factory."""
    monkeypatch.setenv("ISSUE_TRACKER_SERVICE_URL", "http://localhost:8000")

    import issue_tracker_client_api.client as _api  # noqa: PLC0415

    saved = list(_api._factories)
    _api._factories.clear()

    import issue_tracker_client_adapter  # noqa: PLC0415

    importlib.reload(issue_tracker_client_adapter)

    assert isinstance(get_client(), ServiceClientAdapter)

    _api._factories.clear()
    _api._factories.extend(saved)


def test_registered_factory_raises_without_service_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The registered adapter factory fails fast when the service URL is unset."""
    monkeypatch.delenv("ISSUE_TRACKER_SERVICE_URL", raising=False)

    import issue_tracker_client_api.client as _api  # noqa: PLC0415

    import issue_tracker_client_adapter  # noqa: PLC0415

    saved = list(_api._factories)
    _api._factories.clear()
    importlib.reload(issue_tracker_client_adapter)

    with pytest.raises(ValueError, match="ISSUE_TRACKER_SERVICE_URL"):
        _api.get_client()

    _api._factories.clear()
    _api._factories.extend(saved)


@patch("issue_tracker_client_adapter.adapter.get_boards_boards_get")
def test_get_boards(mock_get_boards: MagicMock, adapter: ServiceClientAdapter) -> None:
    """get_boards returns local Board objects converted from the wire model."""
    mock_get_boards.sync.return_value = [
        BoardOut(id="board-1", board_name="Platform"),
        BoardOut(id="board-2", board_name="Ops"),
    ]

    result = list(adapter.get_boards())

    assert result == [
        Board(id="board-1", name="Platform"),
        Board(id="board-2", name="Ops"),
    ]


@patch("issue_tracker_client_adapter.adapter.get_board_boards_board_id_get")
def test_get_board(mock_get_board: MagicMock, adapter: ServiceClientAdapter) -> None:
    """get_board returns a converted local Board."""
    mock_get_board.sync.return_value = BoardOut(id="board-1", board_name="Platform")

    result = adapter.get_board("board-1")

    assert result == Board(id="board-1", name="Platform")


@patch("issue_tracker_client_adapter.adapter.get_board_boards_board_id_get")
def test_get_board_not_found(
    mock_get_board: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """get_board maps service 404s to BoardNotFoundError."""
    mock_get_board.sync.side_effect = errors.UnexpectedStatus(404, b"missing")

    with pytest.raises(BoardNotFoundError):
        adapter.get_board("missing-board")


@patch("issue_tracker_client_adapter.adapter.get_issues_boards_board_id_issues_get")
def test_get_issues_filters_by_status(
    mock_get_issues: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """get_issues applies optional status filtering locally."""
    mock_get_issues.sync.return_value = [
        _issue_out(issue_id="issue-1", status="to_do"),
        _issue_out(issue_id="issue-2", status="in_progress"),
    ]

    result = list(adapter.get_issues("board-1", status=Status.IN_PROGRESS))

    assert result == [
        Issue(
            id="issue-2",
            board_id="board-1",
            title="Test Issue",
            desc="Test Desc",
            status=Status.IN_PROGRESS,
            members=None,
            due_date=None,
        )
    ]


@patch("issue_tracker_client_adapter.adapter.get_issue_issues_issue_id_get")
def test_get_issue(mock_get_issue: MagicMock, adapter: ServiceClientAdapter) -> None:
    """get_issue returns a converted local Issue."""
    mock_get_issue.sync.return_value = _issue_out(status="completed")

    result = adapter.get_issue("issue-1")

    assert result == Issue(
        id="issue-1",
        board_id="board-1",
        title="Test Issue",
        desc="Test Desc",
        status=Status.COMPLETED,
        members=None,
        due_date=None,
    )


@patch("issue_tracker_client_adapter.adapter.get_issue_issues_issue_id_get")
def test_get_issue_not_found(
    mock_get_issue: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """get_issue maps service 404s to IssueNotFoundError."""
    mock_get_issue.sync.side_effect = errors.UnexpectedStatus(404, b"missing")

    with pytest.raises(IssueNotFoundError):
        adapter.get_issue("missing-issue")


@patch("issue_tracker_client_adapter.adapter.create_issue_boards_board_id_issues_post")
def test_create_issue(
    mock_create_issue: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """create_issue sends the new wire payload and returns a converted Issue."""
    mock_create_issue.sync.return_value = _issue_out(
        title="New Issue",
        desc="New Desc",
        status="in_progress",
    )

    result = adapter.create_issue(
        title="New Issue",
        board_id="board-1",
        desc="New Desc",
        status=Status.IN_PROGRESS,
    )

    payload = mock_create_issue.sync.call_args.kwargs["body"]
    assert str(payload.status) == "in_progress"
    assert result == Issue(
        id="issue-1",
        board_id="board-1",
        title="New Issue",
        desc="New Desc",
        status=Status.IN_PROGRESS,
        members=None,
        due_date=None,
    )


@patch("issue_tracker_client_adapter.adapter.create_issue_boards_board_id_issues_post")
def test_create_issue_maps_unexpected_status_to_issue_create_error(
    mock_create_issue: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """create_issue maps unexpected service failures to IssueCreateError."""
    mock_create_issue.sync.side_effect = errors.UnexpectedStatus(404, b"missing board")

    with pytest.raises(IssueCreateError):
        adapter.create_issue(title="New", board_id="missing-board")


@patch("issue_tracker_client_adapter.adapter.update_issue_issues_issue_id_patch")
def test_update_issue(
    mock_update_issue: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """update_issue sends the patch payload and returns a converted Issue."""
    mock_update_issue.sync.return_value = _issue_out(desc="Updated", status="completed")

    result = adapter.update_issue(
        "issue-1",
        desc="Updated",
        status=Status.COMPLETED,
    )

    payload = mock_update_issue.sync.call_args.kwargs["body"]
    assert str(payload.status) == "completed"
    assert result.status == Status.COMPLETED
    assert result.desc == "Updated"


@patch("issue_tracker_client_adapter.adapter.create_board_boards_post")
def test_create_board(
    mock_create_board: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """create_board returns a converted local Board."""
    mock_create_board.sync.return_value = BoardOut(id="board-3", board_name="Infra")

    result = adapter.create_board("Infra")

    payload = mock_create_board.sync.call_args.kwargs["body"]
    assert payload.name == "Infra"
    assert result == Board(id="board-3", name="Infra")


@patch("issue_tracker_client_adapter.adapter.update_board_boards_board_id_patch")
def test_update_board(
    mock_update_board: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """update_board returns a converted local Board."""
    mock_update_board.sync.return_value = BoardOut(
        id="board-1",
        board_name="Platform Eng",
    )

    result = adapter.update_board("board-1", name="Platform Eng")

    payload = mock_update_board.sync.call_args.kwargs["body"]
    assert payload.name == "Platform Eng"
    assert result == Board(id="board-1", name="Platform Eng")


@patch("issue_tracker_client_adapter.adapter.delete_issue_issues_issue_id_delete")
def test_delete_issue(
    mock_delete_issue: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """delete_issue returns the service success flag."""
    mock_delete_issue.sync.return_value = SuccessOut(success=True)

    result = adapter.delete_issue("issue-1")

    assert result is True


@patch("issue_tracker_client_adapter.adapter.delete_board_boards_board_id_delete")
def test_delete_board(
    mock_delete_board: MagicMock,
    adapter: ServiceClientAdapter,
) -> None:
    """delete_board returns the service success flag."""
    mock_delete_board.sync.return_value = SuccessOut(success=True)

    result = adapter.delete_board("board-1")

    assert result is True
