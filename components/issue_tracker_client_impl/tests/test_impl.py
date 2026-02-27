"""Unit tests for DefaultIssueTrackerClient — Trello API mock tests.

Trello API mapping used by DefaultIssueTrackerClient:
  list_issues(board)               -> GET  /1/boards/{board}/cards
  get_issue(board, issue_id)       -> _resolve_card_id + GET  /1/cards/{full_id}
  create_issue(board, title, body) -> GET  /1/boards/{board}/lists
                                      + POST /1/cards
  close_issue(board, issue_id)     -> _resolve_card_id + PUT  /1/cards/{full_id}
  add_comment(board, issue_id, body) -> _resolve_card_id
                                        + POST /1/cards/{full_id}/actions/comments

Authentication: every request carries key=TRELLO_API_KEY and
token=TRELLO_API_TOKEN in query params.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from issue_tracker_client_api.client import Comment, Issue, IssueState
from issue_tracker_client_impl.client import DefaultIssueTrackerClient

FAKE_KEY = "fake-trello-api-key"
FAKE_TOKEN = "fake-trello-api-token" # noqa: S105
BOARD_ID = "board-abc123"
CARD_SHORT_ID = 42
CARD_FULL_ID = "abcdef1234567890abcdef12"
LIST_ID = "list-xyz789"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_card_payload(
    short_id: int = CARD_SHORT_ID,
    name: str = "Default title",
    desc: str = "Default body",
    *,
    closed: bool = False,
) -> dict:
    return {
        "idShort": short_id,
        "id": CARD_FULL_ID,
        "name": name,
        "desc": desc,
        "closed": closed,
    }


def _make_comment_payload(text: str = "A comment") -> dict:
    # last 8 hex chars of CARD_FULL_ID ("abcdef12") → int = 2882400018
    return {"id": CARD_FULL_ID, "data": {"text": text}}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> DefaultIssueTrackerClient:
    """Return a DefaultIssueTrackerClient with both Trello credentials injected."""
    with patch.dict(
        os.environ, {"TRELLO_API_KEY": FAKE_KEY, "TRELLO_API_TOKEN": FAKE_TOKEN}
    ):
        return DefaultIssueTrackerClient()


@pytest.fixture
def mock_requests() -> MagicMock:
    """Patch the entire requests module inside the impl package."""
    with patch("issue_tracker_client_impl.client.requests") as m:
        yield m


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_init_stores_api_key() -> None:
    """TRELLO_API_KEY is stored as _api_key after construction."""
    with patch.dict(
        os.environ, {"TRELLO_API_KEY": FAKE_KEY, "TRELLO_API_TOKEN": FAKE_TOKEN}
    ):
        c = DefaultIssueTrackerClient()
    assert c._api_key == FAKE_KEY


def test_init_stores_api_token() -> None:
    """TRELLO_API_TOKEN is stored as _api_token after construction."""
    with patch.dict(
        os.environ, {"TRELLO_API_KEY": FAKE_KEY, "TRELLO_API_TOKEN": FAKE_TOKEN}
    ):
        c = DefaultIssueTrackerClient()
    assert c._api_token == FAKE_TOKEN


def test_init_raises_when_api_key_missing() -> None:
    """Construction raises KeyError when TRELLO_API_KEY is absent."""
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {"TRELLO_API_KEY", "TRELLO_API_TOKEN"}
    }
    with (
        patch.dict(os.environ, env, clear=True),
        pytest.raises(KeyError, match="TRELLO_API_KEY"),
    ):
        DefaultIssueTrackerClient()


def test_init_raises_when_api_token_missing() -> None:
    """Construction raises KeyError when TRELLO_API_TOKEN is absent."""
    env = {k: v for k, v in os.environ.items() if k != "TRELLO_API_TOKEN"}
    env["TRELLO_API_KEY"] = FAKE_KEY
    with (
        patch.dict(os.environ, env, clear=True),
        pytest.raises(KeyError, match="TRELLO_API_TOKEN"),
    ):
        DefaultIssueTrackerClient()


# ---------------------------------------------------------------------------
# list_issues  →  GET /1/boards/{board}/cards
# ---------------------------------------------------------------------------


def test_list_issues_calls_boards_cards_endpoint(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """list_issues hits GET /1/boards/{board}/cards."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = [
        _make_card_payload(1, "Bug fix", "desc1"),
        _make_card_payload(2, "Feature", "desc2"),
    ]
    mock_requests.get.return_value = mock_resp

    client.list_issues(BOARD_ID)

    mock_requests.get.assert_called_once()
    call_url: str = mock_requests.get.call_args[0][0]
    assert BOARD_ID in call_url
    assert "cards" in call_url


def test_list_issues_passes_auth_params(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """list_issues includes key and token in query params."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = []
    mock_requests.get.return_value = mock_resp

    client.list_issues(BOARD_ID)

    params: dict = mock_requests.get.call_args[1].get("params", {})
    assert params.get("key") == FAKE_KEY
    assert params.get("token") == FAKE_TOKEN


def test_list_issues_returns_open_issues(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """list_issues returns Issue objects with OPEN state parsed from card payloads."""
    expected_issue_count = 2
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = [
        _make_card_payload(1, "Alpha", "body-a"),
        _make_card_payload(2, "Beta", "body-b"),
    ]
    mock_requests.get.return_value = mock_resp

    issues = client.list_issues(BOARD_ID)

    assert isinstance(issues, list)
    assert len(issues) == expected_issue_count
    assert all(isinstance(i, Issue) for i in issues)
    assert issues[0].title == "Alpha"
    assert issues[0].state == IssueState.OPEN
    assert issues[1].title == "Beta"


# ---------------------------------------------------------------------------
# get_issue  →  _resolve_card_id + GET /1/cards/{full_id}
# ---------------------------------------------------------------------------


def test_get_issue_calls_cards_endpoint(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issue hits GET /1/cards/{full_card_id} after resolving the short ID."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_card_payload(
        CARD_SHORT_ID, "Fix login", "details"
    )
    mock_requests.get.return_value = mock_resp

    with patch.object(client, "_resolve_card_id", return_value=CARD_FULL_ID):
        client.get_issue(BOARD_ID, CARD_SHORT_ID)

    mock_requests.get.assert_called_once()
    call_url: str = mock_requests.get.call_args[0][0]
    assert CARD_FULL_ID in call_url


def test_get_issue_returns_correct_issue(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issue maps the Trello card payload to an Issue dataclass."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_card_payload(
        CARD_SHORT_ID, "Fix login", "login details"
    )
    mock_requests.get.return_value = mock_resp

    with patch.object(client, "_resolve_card_id", return_value=CARD_FULL_ID):
        issue = client.get_issue(BOARD_ID, CARD_SHORT_ID)

    assert isinstance(issue, Issue)
    assert issue.title == "Fix login"
    assert issue.body == "login details"
    assert issue.state == IssueState.OPEN


# ---------------------------------------------------------------------------
# create_issue  →  GET /1/boards/{board}/lists + POST /1/cards
# ---------------------------------------------------------------------------


def test_create_issue_posts_to_cards_endpoint(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue hits POST /1/cards after fetching the first open list."""
    lists_resp = MagicMock()
    lists_resp.raise_for_status.return_value = None
    lists_resp.json.return_value = [{"id": LIST_ID}]
    mock_requests.get.return_value = lists_resp

    card_resp = MagicMock()
    card_resp.raise_for_status.return_value = None
    card_resp.json.return_value = _make_card_payload(99, "New issue", "body text")
    mock_requests.post.return_value = card_resp

    client.create_issue(BOARD_ID, "New issue", "body text")

    mock_requests.post.assert_called_once()
    call_url: str = mock_requests.post.call_args[0][0]
    assert "cards" in call_url


def test_create_issue_sends_list_title_body(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue passes idList, name, and desc in query params."""
    lists_resp = MagicMock()
    lists_resp.raise_for_status.return_value = None
    lists_resp.json.return_value = [{"id": LIST_ID}]
    mock_requests.get.return_value = lists_resp

    card_resp = MagicMock()
    card_resp.raise_for_status.return_value = None
    card_resp.json.return_value = _make_card_payload(99, "My title", "My body")
    mock_requests.post.return_value = card_resp

    client.create_issue(BOARD_ID, "My title", "My body")

    params: dict = mock_requests.post.call_args[1].get("params", {})
    assert params.get("idList") == LIST_ID
    assert params.get("name") == "My title"
    assert params.get("desc") == "My body"


def test_create_issue_returns_issue(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue returns an Issue with OPEN state parsed from the created card."""
    lists_resp = MagicMock()
    lists_resp.raise_for_status.return_value = None
    lists_resp.json.return_value = [{"id": LIST_ID}]
    mock_requests.get.return_value = lists_resp

    card_resp = MagicMock()
    card_resp.raise_for_status.return_value = None
    card_resp.json.return_value = _make_card_payload(99, "New issue", "body text")
    mock_requests.post.return_value = card_resp

    issue = client.create_issue(BOARD_ID, "New issue", "body text")

    assert isinstance(issue, Issue)
    assert issue.title == "New issue"
    assert issue.state == IssueState.OPEN


# ---------------------------------------------------------------------------
# close_issue  →  _resolve_card_id + PUT /1/cards/{full_id}
# ---------------------------------------------------------------------------


def test_close_issue_puts_to_card_endpoint(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """close_issue hits PUT /1/cards/{full_card_id}."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_requests.put.return_value = mock_resp

    with patch.object(client, "_resolve_card_id", return_value=CARD_FULL_ID):
        client.close_issue(BOARD_ID, CARD_SHORT_ID)

    mock_requests.put.assert_called_once()
    call_url: str = mock_requests.put.call_args[0][0]
    assert CARD_FULL_ID in call_url


def test_close_issue_sends_closed_true(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """close_issue passes closed='true' in query params."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_requests.put.return_value = mock_resp

    with patch.object(client, "_resolve_card_id", return_value=CARD_FULL_ID):
        client.close_issue(BOARD_ID, CARD_SHORT_ID)

    params: dict = mock_requests.put.call_args[1].get("params", {})
    assert params.get("closed") == "true"


def test_close_issue_returns_true(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """close_issue returns True on success."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_requests.put.return_value = mock_resp

    with patch.object(client, "_resolve_card_id", return_value=CARD_FULL_ID):
        result = client.close_issue(BOARD_ID, CARD_SHORT_ID)

    assert result is True


# ---------------------------------------------------------------------------
# add_comment  →  _resolve_card_id + POST /1/cards/{full_id}/actions/comments
# ---------------------------------------------------------------------------


def test_add_comment_posts_to_actions_comments(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """add_comment hits POST /1/cards/{full_card_id}/actions/comments."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_comment_payload("Great work!")
    mock_requests.post.return_value = mock_resp

    with patch.object(client, "_resolve_card_id", return_value=CARD_FULL_ID):
        client.add_comment(BOARD_ID, CARD_SHORT_ID, "Great work!")

    mock_requests.post.assert_called_once()
    call_url: str = mock_requests.post.call_args[0][0]
    assert CARD_FULL_ID in call_url
    assert "comments" in call_url


def test_add_comment_sends_text_as_param(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """add_comment passes text=body in query params."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_comment_payload("LGTM")
    mock_requests.post.return_value = mock_resp

    with patch.object(client, "_resolve_card_id", return_value=CARD_FULL_ID):
        client.add_comment(BOARD_ID, CARD_SHORT_ID, "LGTM")

    params: dict = mock_requests.post.call_args[1].get("params", {})
    assert params.get("text") == "LGTM"


def test_add_comment_returns_comment(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """add_comment returns a Comment parsed from the Trello action payload."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_comment_payload("Looks good!")
    mock_requests.post.return_value = mock_resp

    with patch.object(client, "_resolve_card_id", return_value=CARD_FULL_ID):
        comment = client.add_comment(BOARD_ID, CARD_SHORT_ID, "Looks good!")

    assert isinstance(comment, Comment)
    assert comment.body == "Looks good!"
