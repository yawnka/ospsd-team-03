"""Tests for the ServiceClientAdapter."""

from unittest.mock import MagicMock, patch

import pytest

from issue_tracker_client_adapter.adapter import ServiceClientAdapter
from issue_tracker_client_api.client import Comment, Issue, IssueState


@pytest.fixture
def adapter() -> ServiceClientAdapter:
    return ServiceClientAdapter(base_url="http://localhost:8000")


@patch(
    "issue_tracker_client_adapter.adapter.list_issues_boards_board_issues_get"
)
def test_list_issues(mock_list: MagicMock, adapter: ServiceClientAdapter) -> None:
    mock_issue = MagicMock()
    mock_issue.id = 1
    mock_issue.title = "Test Issue"
    mock_issue.body = "Test Body"
    mock_issue.state = "open"
    mock_list.sync.return_value = [mock_issue]

    result = adapter.list_issues("test-board")

    assert len(result) == 1
    assert result[0] == Issue(id=1, title="Test Issue", body="Test Body", state=IssueState.OPEN)


@patch(
    "issue_tracker_client_adapter.adapter.list_issues_boards_board_issues_get"
)
def test_list_issues_empty(mock_list: MagicMock, adapter: ServiceClientAdapter) -> None:
    mock_list.sync.return_value = None

    result = adapter.list_issues("test-board")

    assert result == []


@patch(
    "issue_tracker_client_adapter.adapter.get_issue_boards_board_issues_issue_id_get"
)
def test_get_issue(mock_get: MagicMock, adapter: ServiceClientAdapter) -> None:
    mock_issue = MagicMock()
    mock_issue.id = 1
    mock_issue.title = "Test Issue"
    mock_issue.body = "Test Body"
    mock_issue.state = "open"
    mock_get.sync.return_value = mock_issue

    result = adapter.get_issue("test-board", 1)

    assert result == Issue(id=1, title="Test Issue", body="Test Body", state=IssueState.OPEN)


@patch(
    "issue_tracker_client_adapter.adapter.get_issue_boards_board_issues_issue_id_get"
)
def test_get_issue_not_found(mock_get: MagicMock, adapter: ServiceClientAdapter) -> None:
    mock_get.sync.return_value = None

    with pytest.raises(KeyError):
        adapter.get_issue("test-board", 999)


@patch(
    "issue_tracker_client_adapter.adapter.create_issue_boards_board_issues_post"
)
def test_create_issue(mock_create: MagicMock, adapter: ServiceClientAdapter) -> None:
    mock_issue = MagicMock()
    mock_issue.id = 2
    mock_issue.title = "New Issue"
    mock_issue.body = "New Body"
    mock_issue.state = "open"
    mock_create.sync.return_value = mock_issue

    result = adapter.create_issue("test-board", "New Issue", "New Body")

    assert result == Issue(id=2, title="New Issue", body="New Body", state=IssueState.OPEN)


@patch(
    "issue_tracker_client_adapter.adapter.close_issue_boards_board_issues_issue_id_close_post"
)
def test_close_issue(mock_close: MagicMock, adapter: ServiceClientAdapter) -> None:
    mock_close.sync.return_value = {"success": True}

    result = adapter.close_issue("test-board", 1)

    assert result is True


@patch(
    "issue_tracker_client_adapter.adapter.add_comment_boards_board_issues_issue_id_comments_post"
)
def test_add_comment(mock_comment: MagicMock, adapter: ServiceClientAdapter) -> None:
    mock_response = MagicMock()
    mock_response.id = 1
    mock_response.body = "Test comment"
    mock_comment.sync.return_value = mock_response

    result = adapter.add_comment("test-board", 1, "Test comment")

    assert result == Comment(id=1, body="Test comment")
