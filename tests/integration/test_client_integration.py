"""Integration tests for Trello client authentication and API connectivity.

This module tests that the dependency injection works correctly and that
the client can authenticate and make real API calls to Trello.
"""

import os

import issue_tracker_client_api.client as _api
import pytest
from issue_tracker_client_api.client import Comment, Issue, IssueState
from issue_tracker_client_impl.client import DefaultIssueTrackerClient


def _skip_if_no_credentials() -> None:
    """Skip test if Trello credentials are not available."""
    if not os.environ.get("TRELLO_API_KEY") or not os.environ.get("TRELLO_API_TOKEN"):
        pytest.skip("Trello credentials not available")


def _get_board_id() -> str:
    """Return the board ID from env, or skip."""
    board_id = os.environ.get("TRELLO_BOARD_ID", "")
    if not board_id:
        pytest.skip("TRELLO_BOARD_ID not set")
    return board_id


def test_get_client_and_authenticate() -> None:
    """DI provides a real, authenticated DefaultIssueTrackerClient."""
    _skip_if_no_credentials()
    try:
        client = _api.get_client()
        assert isinstance(client, DefaultIssueTrackerClient)
    except (RuntimeError, KeyError) as e:
        pytest.fail(f"Integration test failed during authentication: {e}")


def test_list_issues_returns_real_data() -> None:
    """list_issues returns a list of Issue objects from the real board."""
    _skip_if_no_credentials()
    board_id = _get_board_id()
    client = _api.get_client()

    issues = client.list_issues(board_id)

    assert isinstance(issues, list)
    for issue in issues:
        assert isinstance(issue, Issue)
        assert isinstance(issue.id, int)
        assert isinstance(issue.title, str)
        assert issue.state in (IssueState.OPEN, IssueState.CLOSED)


def test_create_and_close_issue_lifecycle() -> None:
    """Create a card, verify it, then close it — full lifecycle."""
    _skip_if_no_credentials()
    board_id = _get_board_id()
    client = _api.get_client()

    # Create
    created = client.create_issue(board_id, "CI integration test", "auto-created")
    assert isinstance(created, Issue)
    assert created.title == "CI integration test"
    assert created.state == IssueState.OPEN

    # Get
    fetched = client.get_issue(board_id, created.id)
    assert fetched.id == created.id
    assert fetched.title == created.title

    # Close
    result = client.close_issue(board_id, created.id)
    assert result is True


def test_add_comment_to_real_card() -> None:
    """Create a card, add a comment, then clean up."""
    _skip_if_no_credentials()
    board_id = _get_board_id()
    client = _api.get_client()

    # Create a card to comment on
    card = client.create_issue(board_id, "CI comment test", "auto-created")

    # Add comment
    comment = client.add_comment(board_id, card.id, "integration test comment")
    assert isinstance(comment, Comment)
    assert comment.body == "integration test comment"

    # Clean up
    client.close_issue(board_id, card.id)
