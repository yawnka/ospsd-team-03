"""Unit tests for DefaultIssueTrackerClient — Trello API mock tests.

Trello API mapping used by DefaultIssueTrackerClient:
  get_boards()                          -> GET  /1/members/me/boards
  get_board(board_id)                   -> GET  /1/boards/{board_id}
  get_issues(board_id, status=None)     -> GET  /1/boards/{board_id}/lists
                                           GET  /1/boards/{board_id}/cards
  get_issue(issue_id)                   -> GET  /1/cards/{issue_id}
                                           GET  /1/lists/{list_id}
  create_issue(board_id, title, desc)   -> GET  /1/boards/{board_id}/lists
                                           POST /1/cards
  update_issue_status(issue_id, status) -> GET  /1/cards/{issue_id}
                                           GET  /1/boards/{board_id}/lists
                                           PUT  /1/cards/{issue_id}
  delete_issue(issue_id)                -> PUT  /1/cards/{issue_id}

Authentication: every request carries key=TRELLO_API_KEY and
token=TRELLO_API_TOKEN in query params.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from issue_tracker_client_api.client import (
    Board,
    BoardNotFoundError,
    Issue,
    IssueNotFoundError,
    Status,
)
from issue_tracker_client_impl.client import DefaultIssueTrackerClient

pytestmark = pytest.mark.unit

FAKE_KEY = "fake-trello-api-key"
FAKE_TOKEN = "fake-trello-api-token" # noqa: S105
BOARD_ID = "board-abc123"
BOARD_ID_2 = "board-def456"
CARD_ID = "abcdef1234567890abcdef12"
LIST_ID_TODO = "list-todo-111"
LIST_ID_INPROG = "list-inprog-222"
LIST_ID_DONE = "list-done-333"


# ---------------------------------------------------------------------------
# Payload factories
# ---------------------------------------------------------------------------


def _resp(json_data: object = None) -> MagicMock:
    """Return a mock HTTP response with the given JSON body."""
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = json_data
    return m


def _err_resp(status_code: int) -> MagicMock:
    """Return a mock HTTP response whose raise_for_status raises HTTPError."""
    exc = requests.HTTPError()
    exc.response = MagicMock()
    exc.response.status_code = status_code
    m = MagicMock()
    m.raise_for_status.side_effect = exc
    return m


def _board(board_id: str = BOARD_ID, name: str = "My Board") -> dict:
    return {"id": board_id, "name": name}


def _list_payload(list_id: str, name: str) -> dict:
    return {"id": list_id, "name": name}


def _card(
    card_id: str = CARD_ID,
    board_id: str = BOARD_ID,
    name: str = "Default title",
    desc: str = "Default desc",
    id_list: str = LIST_ID_TODO,
) -> dict:
    return {
        "id": card_id,
        "idBoard": board_id,
        "name": name,
        "desc": desc,
        "idList": id_list,
    }


_LISTS = [
    _list_payload(LIST_ID_TODO, "To Do"),
    _list_payload(LIST_ID_INPROG, "In Progress"),
    _list_payload(LIST_ID_DONE, "Done"),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> DefaultIssueTrackerClient:
    """Return a DefaultIssueTrackerClient with test credentials."""
    return DefaultIssueTrackerClient(api_key=FAKE_KEY, token=FAKE_TOKEN)


@pytest.fixture
def mock_requests() -> MagicMock:
    """Patch the entire requests module inside the impl package.

    The real requests.HTTPError is restored on the mock so that
    ``except requests.HTTPError`` clauses in the impl work correctly.
    """
    with patch("issue_tracker_client_impl.client.requests") as m:
        m.HTTPError = requests.HTTPError
        yield m


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_init_stores_api_key() -> None:
    """api_key is stored as _api_key after construction."""
    c = DefaultIssueTrackerClient(api_key=FAKE_KEY, token=FAKE_TOKEN)
    assert c._api_key == FAKE_KEY


def test_init_stores_api_token() -> None:
    """Token is stored as _api_token after construction."""
    c = DefaultIssueTrackerClient(api_key=FAKE_KEY, token=FAKE_TOKEN)
    assert c._api_token == FAKE_TOKEN


def test_init_raises_when_api_key_missing() -> None:
    """Construction raises TypeError when api_key is not provided."""
    with pytest.raises(TypeError):
        DefaultIssueTrackerClient(token=FAKE_TOKEN)  # type: ignore[call-arg]


def test_init_raises_when_api_token_missing() -> None:
    """Construction raises TypeError when token is not provided."""
    with pytest.raises(TypeError):
        DefaultIssueTrackerClient(api_key=FAKE_KEY)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# get_boards  ->  GET /1/members/me/boards
# ---------------------------------------------------------------------------


def test_get_boards_calls_members_me_boards(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_boards hits GET /1/members/me/boards."""
    mock_requests.get.return_value = _resp([_board(BOARD_ID, "Alpha")])

    client.get_boards()

    url: str = mock_requests.get.call_args[0][0]
    assert "members/me/boards" in url


def test_get_boards_passes_auth_params(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_boards includes key and token in query params."""
    mock_requests.get.return_value = _resp([])

    client.get_boards()

    params: dict = mock_requests.get.call_args[1]["params"]
    assert params["key"] == FAKE_KEY
    assert params["token"] == FAKE_TOKEN


def test_get_boards_returns_board_list(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_boards returns an iterator of Board dataclasses with correct fields."""
    mock_requests.get.return_value = _resp(
        [_board(BOARD_ID, "Alpha"), _board(BOARD_ID_2, "Beta")]
    )

    boards = list(client.get_boards())

    assert len(boards) == 2  # noqa: PLR2004
    assert all(isinstance(b, Board) for b in boards)
    assert boards[0].id == BOARD_ID
    assert boards[0].name == "Alpha"
    assert boards[1].id == BOARD_ID_2
    assert boards[1].name == "Beta"


def test_get_boards_returns_empty_when_none(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_boards returns an empty iterator when the member has no boards."""
    mock_requests.get.return_value = _resp([])

    boards = list(client.get_boards())

    assert boards == []


# ---------------------------------------------------------------------------
# get_board  ->  GET /1/boards/{board_id}
# ---------------------------------------------------------------------------


def test_get_board_calls_boards_endpoint(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_board hits GET /1/boards/{board_id}."""
    mock_requests.get.return_value = _resp(_board())

    client.get_board(BOARD_ID)

    url: str = mock_requests.get.call_args[0][0]
    assert BOARD_ID in url


def test_get_board_returns_board(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_board returns a Board with id and name populated."""
    mock_requests.get.return_value = _resp(_board(BOARD_ID, "My Board"))

    board = client.get_board(BOARD_ID)

    assert isinstance(board, Board)
    assert board.id == BOARD_ID
    assert board.name == "My Board"


def test_get_board_raises_board_not_found_on_404(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_board raises BoardNotFoundError when Trello returns 404."""
    mock_requests.get.return_value = _err_resp(404)

    with pytest.raises(BoardNotFoundError):
        client.get_board(BOARD_ID)


# ---------------------------------------------------------------------------
# get_issues  ->  GET /1/boards/{board_id}/lists + GET /1/boards/{board_id}/cards
# ---------------------------------------------------------------------------


def test_get_issues_calls_lists_then_cards_endpoints(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issues fetches board lists, then cards, in two GET calls."""
    mock_requests.get.side_effect = [
        _resp(_LISTS),
        _resp([_card()]),
    ]

    client.get_issues(BOARD_ID)

    assert mock_requests.get.call_count == 2  # noqa: PLR2004
    first_url: str = mock_requests.get.call_args_list[0][0][0]
    second_url: str = mock_requests.get.call_args_list[1][0][0]
    assert "lists" in first_url
    assert "cards" in second_url


def test_get_issues_returns_issues_with_board_id(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issues returns Issue objects that each carry board_id."""
    mock_requests.get.side_effect = [
        _resp(_LISTS),
        _resp([
            _card(id_list=LIST_ID_TODO),
            _card(card_id="other-id", id_list=LIST_ID_INPROG),
        ]),
    ]

    issues = list(client.get_issues(BOARD_ID))

    assert len(issues) == 2  # noqa: PLR2004
    assert all(isinstance(i, Issue) for i in issues)
    assert all(i.board_id == BOARD_ID for i in issues)


def test_get_issues_maps_list_name_to_status(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issues resolves each card's list name to the correct canonical Status."""
    mock_requests.get.side_effect = [
        _resp(_LISTS),
        _resp([
            _card(card_id="c1", id_list=LIST_ID_TODO),
            _card(card_id="c2", id_list=LIST_ID_INPROG),
            _card(card_id="c3", id_list=LIST_ID_DONE),
        ]),
    ]

    issues = list(client.get_issues(BOARD_ID))

    statuses = {i.id: i.status for i in issues}
    assert statuses["c1"] == Status.TO_DO
    assert statuses["c2"] == Status.IN_PROGRESS
    assert statuses["c3"] == Status.COMPLETED


def test_get_issues_filters_by_status(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issues returns only issues matching the requested Status."""
    mock_requests.get.side_effect = [
        _resp(_LISTS),
        _resp([
            _card(card_id="c1", id_list=LIST_ID_TODO),
            _card(card_id="c2", id_list=LIST_ID_INPROG),
        ]),
    ]

    issues = list(client.get_issues(BOARD_ID, status=Status.IN_PROGRESS))

    assert len(issues) == 1
    assert issues[0].id == "c2"
    assert issues[0].status == Status.IN_PROGRESS


def test_get_issues_passes_auth_params(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issues includes key and token in every GET request."""
    mock_requests.get.side_effect = [_resp(_LISTS), _resp([])]

    client.get_issues(BOARD_ID)

    for call in mock_requests.get.call_args_list:
        params: dict = call[1]["params"]
        assert params["key"] == FAKE_KEY
        assert params["token"] == FAKE_TOKEN


# ---------------------------------------------------------------------------
# get_issue  ->  GET /1/cards/{id} + GET /1/lists/{idList}
# ---------------------------------------------------------------------------


def test_get_issue_calls_cards_endpoint(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issue hits GET /1/cards/{issue_id} as its first request."""
    mock_requests.get.side_effect = [
        _resp(_card()),
        _resp({"name": "To Do"}),
    ]

    client.get_issue(CARD_ID)

    first_url: str = mock_requests.get.call_args_list[0][0][0]
    assert CARD_ID in first_url


def test_get_issue_fetches_list_name(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issue fetches the card's list name to determine status."""
    mock_requests.get.side_effect = [
        _resp(_card(id_list=LIST_ID_INPROG)),
        _resp({"name": "In Progress"}),
    ]

    client.get_issue(CARD_ID)

    second_url: str = mock_requests.get.call_args_list[1][0][0]
    assert LIST_ID_INPROG in second_url


def test_get_issue_returns_correct_issue(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issue returns an Issue with all fields populated, including board_id."""
    mock_requests.get.side_effect = [
        _resp(_card(name="Fix login bug", desc="Details here", id_list=LIST_ID_DONE)),
        _resp({"name": "Done"}),
    ]

    issue = client.get_issue(CARD_ID)

    assert isinstance(issue, Issue)
    assert issue.id == CARD_ID
    assert issue.board_id == BOARD_ID
    assert issue.title == "Fix login bug"
    assert issue.desc == "Details here"
    assert issue.status == Status.COMPLETED


def test_get_issue_raises_issue_not_found_on_404(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issue raises IssueNotFoundError when Trello returns 404."""
    mock_requests.get.return_value = _err_resp(404)

    with pytest.raises(IssueNotFoundError):
        client.get_issue(CARD_ID)


def test_get_issue_raises_issue_not_found_on_400(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """get_issue raises IssueNotFoundError when Trello returns 400 (bad card ID)."""
    mock_requests.get.return_value = _err_resp(400)

    with pytest.raises(IssueNotFoundError):
        client.get_issue("bad-id")


# ---------------------------------------------------------------------------
# create_issue  ->  GET /1/boards/{board_id}/lists + POST /1/cards
# ---------------------------------------------------------------------------


def test_create_issue_posts_to_cards_endpoint(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue hits POST /1/cards after fetching the board's lists."""
    mock_requests.get.return_value = _resp(_LISTS)
    mock_requests.post.return_value = _resp(_card(name="New issue", desc="body text"))

    client.create_issue("New issue", BOARD_ID, desc="body text")

    mock_requests.post.assert_called_once()
    url: str = mock_requests.post.call_args[0][0]
    assert "cards" in url


def test_create_issue_sends_list_id_name_desc(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue passes idList, name, and desc in the POST params."""
    mock_requests.get.return_value = _resp(_LISTS)
    mock_requests.post.return_value = _resp(_card(name="My title", desc="My desc"))

    client.create_issue("My title", BOARD_ID, desc="My desc")

    params: dict = mock_requests.post.call_args[1]["params"]
    assert params["idList"] == LIST_ID_TODO
    assert params["name"] == "My title"
    assert params["desc"] == "My desc"


def test_create_issue_prefers_to_do_list(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue places the card in the first list that maps to to_do."""
    lists_with_todo_second = [
        _list_payload("other-list", "In Progress"),  # maps to in_progress, not to_do
        _list_payload(LIST_ID_TODO, "To Do"),
    ]
    mock_requests.get.return_value = _resp(lists_with_todo_second)
    mock_requests.post.return_value = _resp(_card(id_list=LIST_ID_TODO))

    client.create_issue("Title", BOARD_ID, desc="Desc")

    params: dict = mock_requests.post.call_args[1]["params"]
    assert params["idList"] == LIST_ID_TODO


def test_create_issue_falls_back_to_first_list_when_no_todo(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue uses the first list when no list maps to to_do."""
    lists_no_todo = [
        _list_payload("first-id", "Miscellaneous"),
        _list_payload("second-id", "In Progress"),
    ]
    mock_requests.get.return_value = _resp(lists_no_todo)
    mock_requests.post.return_value = _resp(_card(id_list="first-id"))

    client.create_issue("Title", BOARD_ID, desc="Desc")

    params: dict = mock_requests.post.call_args[1]["params"]
    assert params["idList"] == "first-id"


def test_create_issue_returns_issue_with_board_id(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue returns an Issue with board_id and status populated."""
    mock_requests.get.return_value = _resp(_LISTS)
    mock_requests.post.return_value = _resp(_card(name="New issue", desc="body"))

    issue = client.create_issue("New issue", BOARD_ID, desc="body")

    assert isinstance(issue, Issue)
    assert issue.board_id == BOARD_ID
    assert issue.title == "New issue"
    assert issue.status == Status.TO_DO


def test_create_issue_raises_when_no_lists(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """create_issue raises ValueError when the board has no open lists."""
    mock_requests.get.return_value = _resp([])

    with pytest.raises(ValueError, match="no open lists"):
        client.create_issue("Title", BOARD_ID, desc="Desc")


# ---------------------------------------------------------------------------
# update_issue  ->  GET /cards/{id} + GET /boards/{id}/lists + PUT /cards/{id}
# ---------------------------------------------------------------------------


def test_update_issue_moves_card_to_correct_list(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """update_issue puts the card into the list matching the target status."""
    updated_card = _card(id_list=LIST_ID_DONE)
    mock_requests.get.side_effect = [
        _resp(_card(id_list=LIST_ID_TODO)),   # GET card for idBoard
        _resp(_LISTS),                          # GET board lists
        _resp({"name": "Done"}),               # GET list name after PUT
    ]
    mock_requests.put.return_value = _resp(updated_card)

    client.update_issue(CARD_ID, status=Status.COMPLETED)

    params: dict = mock_requests.put.call_args[1]["params"]
    assert params["idList"] == LIST_ID_DONE


def test_update_issue_calls_put_on_card(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """update_issue sends PUT to /1/cards/{issue_id}."""
    mock_requests.get.side_effect = [
        _resp(_card()),
        _resp(_LISTS),
        _resp({"name": "In Progress"}),
    ]
    mock_requests.put.return_value = _resp(_card(id_list=LIST_ID_INPROG))

    client.update_issue(CARD_ID, status=Status.IN_PROGRESS)

    url: str = mock_requests.put.call_args[0][0]
    assert CARD_ID in url


def test_update_issue_returns_updated_issue(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """update_issue returns an Issue reflecting the new status."""
    mock_requests.get.side_effect = [
        _resp(_card(id_list=LIST_ID_TODO)),   # GET card for idBoard
        _resp(_LISTS),                          # GET board lists
        _resp({"name": "In Progress"}),        # GET list name after PUT
    ]
    mock_requests.put.return_value = _resp(
        _card(id_list=LIST_ID_INPROG, name="My card")
    )

    issue = client.update_issue(CARD_ID, status=Status.IN_PROGRESS)

    assert isinstance(issue, Issue)
    assert issue.id == CARD_ID
    assert issue.board_id == BOARD_ID
    assert issue.status == Status.IN_PROGRESS
    assert issue.title == "My card"


def test_update_issue_raises_issue_not_found_on_404(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """update_issue raises IssueNotFoundError when the card does not exist."""
    mock_requests.get.return_value = _err_resp(404)
    mock_requests.put.return_value = _err_resp(404)

    with pytest.raises(IssueNotFoundError):
        client.update_issue(CARD_ID, status=Status.COMPLETED)


def test_update_issue_updates_title_only(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """update_issue sends only changed fields; omits idList when status not given."""
    updated_card = _card(name="New Title", id_list=LIST_ID_TODO)
    mock_requests.get.return_value = _resp({"name": "To Do"})  # GET list name after PUT
    mock_requests.put.return_value = _resp(updated_card)

    issue = client.update_issue(CARD_ID, title="New Title")

    params: dict = mock_requests.put.call_args[1]["params"]
    assert params["name"] == "New Title"
    assert "idList" not in params
    assert issue.title == "New Title"


# ---------------------------------------------------------------------------
# delete_issue  ->  PUT /1/cards/{issue_id}?closed=true
# ---------------------------------------------------------------------------


def test_delete_issue_puts_closed_true(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """delete_issue sends PUT /1/cards/{id} with closed='true'."""
    mock_requests.put.return_value = _resp(_card())

    client.delete_issue(CARD_ID)

    mock_requests.put.assert_called_once()
    url: str = mock_requests.put.call_args[0][0]
    assert CARD_ID in url
    params: dict = mock_requests.put.call_args[1]["params"]
    assert params["closed"] == "true"


def test_delete_issue_returns_true(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """delete_issue returns True on success."""
    mock_requests.put.return_value = _resp(_card())

    result = client.delete_issue(CARD_ID)

    assert result is True


def test_delete_issue_raises_issue_not_found_on_404(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """delete_issue raises IssueNotFoundError when Trello returns 404."""
    mock_requests.put.return_value = _err_resp(404)

    with pytest.raises(IssueNotFoundError):
        client.delete_issue(CARD_ID)


def test_delete_issue_raises_issue_not_found_on_400(
    client: DefaultIssueTrackerClient,
    mock_requests: MagicMock,
) -> None:
    """delete_issue raises IssueNotFoundError when Trello returns 400."""
    mock_requests.put.return_value = _err_resp(400)

    with pytest.raises(IssueNotFoundError):
        client.delete_issue("bad-id")
