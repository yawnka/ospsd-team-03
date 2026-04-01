"""Tests for the ServiceClientAdapter."""

from unittest.mock import MagicMock, patch

import pytest

from issue_tracker_client_adapter.adapter import ServiceClientAdapter
from issue_tracker_client_api.client import (
    Comment,
    Issue,
    IssueNotFoundError,
    IssueState,
    get_client,
)
from issue_tracker_client_service_client.models import (
    CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost as CloseIssueResponse,  # noqa: E501
    CommentOut,
    IssueOut,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def adapter() -> ServiceClientAdapter:
    """Return a ServiceClientAdapter instance."""
    return ServiceClientAdapter(base_url="http://localhost:8000")


# ---------------------------------------------------------------------------
# DI registration
# ---------------------------------------------------------------------------


def test_import_registers_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Importing the adapter package registers ServiceClientAdapter as the factory."""
    monkeypatch.setenv("ISSUE_TRACKER_SERVICE_URL", "http://localhost:8000")

    import issue_tracker_client_api.client as _api  # noqa: PLC0415

    # Clear existing factories so the adapter is the only one registered
    saved = list(_api._factories)
    _api._factories.clear()

    import importlib  # noqa: PLC0415

    import issue_tracker_client_adapter  # noqa: PLC0415

    importlib.reload(issue_tracker_client_adapter)

    assert isinstance(get_client(), ServiceClientAdapter)

    # Restore original factories so other tests are not affected
    _api._factories.clear()
    _api._factories.extend(saved)


# ---------------------------------------------------------------------------
# list_issues
# ---------------------------------------------------------------------------


@patch("issue_tracker_client_adapter.adapter.list_issues_boards_board_issues_get")
def test_list_issues(mock_list: MagicMock, adapter: ServiceClientAdapter) -> None:
    """Test listing issues returns correct Issue objects."""
    mock_issue = MagicMock(spec=IssueOut)
    mock_issue.id = 1
    mock_issue.title = "Test Issue"
    mock_issue.body = "Test Body"
    mock_issue.state = "open"
    mock_list.sync.return_value = [mock_issue]

    result = adapter.list_issues("test-board")

    assert len(result) == 1
    assert result[0] == Issue(
        id=1, title="Test Issue", body="Test Body", state=IssueState.OPEN
    )


@patch("issue_tracker_client_adapter.adapter.list_issues_boards_board_issues_get")
def test_list_issues_empty(mock_list: MagicMock, adapter: ServiceClientAdapter) -> None:
    """Test listing issues returns empty list when response is None."""
    mock_list.sync.return_value = None

    result = adapter.list_issues("test-board")

    assert result == []


# ---------------------------------------------------------------------------
# get_issue
# ---------------------------------------------------------------------------


@patch(
    "issue_tracker_client_adapter.adapter.get_issue_boards_board_issues_issue_id_get"
)
def test_get_issue(mock_get: MagicMock, adapter: ServiceClientAdapter) -> None:
    """Test getting a single issue returns correct Issue object."""
    mock_issue = MagicMock(spec=IssueOut)
    mock_issue.id = 1
    mock_issue.title = "Test Issue"
    mock_issue.body = "Test Body"
    mock_issue.state = "open"
    mock_get.sync.return_value = mock_issue

    result = adapter.get_issue("test-board", 1)

    assert result == Issue(
        id=1, title="Test Issue", body="Test Body", state=IssueState.OPEN
    )


@patch(
    "issue_tracker_client_adapter.adapter.get_issue_boards_board_issues_issue_id_get"
)
def test_get_issue_not_found(
    mock_get: MagicMock, adapter: ServiceClientAdapter
) -> None:
    """Test getting a non-existent issue raises IssueNotFoundError."""
    mock_get.sync.return_value = None

    with pytest.raises(IssueNotFoundError):
        adapter.get_issue("test-board", 999)


# ---------------------------------------------------------------------------
# create_issue
# ---------------------------------------------------------------------------


@patch("issue_tracker_client_adapter.adapter.create_issue_boards_board_issues_post")
def test_create_issue(mock_create: MagicMock, adapter: ServiceClientAdapter) -> None:
    """Test creating an issue returns correct Issue object."""
    mock_issue = MagicMock(spec=IssueOut)
    mock_issue.id = 2
    mock_issue.title = "New Issue"
    mock_issue.body = "New Body"
    mock_issue.state = "open"
    mock_create.sync.return_value = mock_issue

    result = adapter.create_issue("test-board", "New Issue", "New Body")

    assert result == Issue(
        id=2, title="New Issue", body="New Body", state=IssueState.OPEN
    )


# ---------------------------------------------------------------------------
# close_issue
# ---------------------------------------------------------------------------


@patch(
    "issue_tracker_client_adapter.adapter"
    ".close_issue_boards_board_issues_issue_id_close_post"
)
def test_close_issue(mock_close: MagicMock, adapter: ServiceClientAdapter) -> None:
    """Test closing an issue returns True on success."""
    mock_response = MagicMock(spec=CloseIssueResponse)
    mock_response.additional_properties = {"success": True}
    mock_close.sync.return_value = mock_response

    result = adapter.close_issue("test-board", 1)

    assert result is True


@patch(
    "issue_tracker_client_adapter.adapter"
    ".close_issue_boards_board_issues_issue_id_close_post"
)
def test_close_issue_not_found(
    mock_close: MagicMock, adapter: ServiceClientAdapter
) -> None:
    """Test closing an issue returns False when the response is None."""
    mock_close.sync.return_value = None

    result = adapter.close_issue("test-board", 999)

    assert result is False


# ---------------------------------------------------------------------------
# add_comment
# ---------------------------------------------------------------------------


@patch(
    "issue_tracker_client_adapter.adapter"
    ".add_comment_boards_board_issues_issue_id_comments_post"
)
def test_add_comment(mock_comment: MagicMock, adapter: ServiceClientAdapter) -> None:
    """Test adding a comment returns correct Comment object."""
    mock_response = MagicMock(spec=CommentOut)
    mock_response.id = 1
    mock_response.body = "Test comment"
    mock_comment.sync.return_value = mock_response

    result = adapter.add_comment("test-board", 1, "Test comment")

    assert result == Comment(id=1, body="Test comment")
