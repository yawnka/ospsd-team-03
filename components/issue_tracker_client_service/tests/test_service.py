"""Unit tests for the issue tracker client service."""

from dataclasses import dataclass
from enum import Enum
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from issue_tracker_client_api.client import BoardNotFoundError, IssueNotFoundError
from issue_tracker_client_impl.client import DefaultIssueTrackerClient
from issue_tracker_client_service.app import app
from issue_tracker_client_service.auth import consume_state, create_state
from issue_tracker_client_service.session import get_session, save_session

from issue_tracker_client_service import app as app_module

pytestmark = pytest.mark.unit

HTTP_OK = 200
HTTP_FOUND = 302
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_INTERNAL_SERVER_ERROR = 500

EXPECTED_BOARD_COUNT = 2
EXPECTED_ISSUE_COUNT = 2
SERVICE_ENV = {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"}

client = TestClient(app)


def test_health() -> None:
    """Health endpoint returns OK."""
    response = client.get("/health")

    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "ok"}


def test_create_and_consume_state() -> None:
    """Create and consume a valid OAuth state."""
    state = create_state()
    consume_state(state)


def test_consume_invalid_state_raises() -> None:
    """Invalid state raises an exception."""
    with pytest.raises(Exception, match="Invalid OAuth state"):
        consume_state("invalid-state")


def test_auth_login_redirects() -> None:
    """Login endpoint redirects to Trello auth."""
    with patch.object(
        app_module,
        "build_authorization_url",
        return_value="https://trello.com/1/authorize?key=abc",
    ):
        response = client.get("/auth/login", follow_redirects=False)

    assert response.status_code == HTTP_FOUND
    assert "trello.com" in response.headers["location"]


def test_auth_callback_returns_html() -> None:
    """Callback returns HTML page for token extraction."""
    state = create_state()
    response = client.get(
        "/auth/callback",
        params={"state": state},
    )
    assert response.status_code == HTTP_OK
    assert "text/html" in response.headers["content-type"]
    assert "token" in response.text


def test_auth_callback_missing_state_returns_400() -> None:
    """Callback without state returns 400."""
    response = client.get("/auth/callback")
    assert response.status_code == HTTP_BAD_REQUEST


def test_auth_token_saves_session() -> None:
    """Token endpoint saves session and returns session_id."""
    response = client.post(
        "/auth/token",
        json={"token": "trello-user-token"},
    )
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["status"] == "authenticated"
    assert data["session_id"] is not None

    session = get_session(data["session_id"])
    assert session is not None
    assert session.access_token == "trello-user-token"  # noqa: S105


def test_auth_token_missing_token_returns_422() -> None:
    """Token endpoint without required token field returns 422 validation error."""
    response = client.post("/auth/token", json={})
    assert response.status_code == HTTP_UNPROCESSABLE_ENTITY


class FakeStatus(Enum):
    """Fake shared status values."""

    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class FakeBoard:
    """Fake board model."""

    id: str
    board_name: str


@dataclass
class FakeIssue:
    """Fake issue model."""

    id: str
    title: str
    desc: str
    members: list[str] | None
    due_date: str | None
    status: FakeStatus
    board_id: str


class FakeClient:
    """Fake shared-contract client for endpoint tests."""

    def __init__(self) -> None:
        """Seed fake boards and issues for endpoint tests."""
        self._boards = {
            "board-1": FakeBoard(id="board-1", board_name="Platform"),
            "board-2": FakeBoard(id="board-2", board_name="Ops"),
        }
        self._issues = {
            "issue-1": FakeIssue(
                id="issue-1",
                title="Issue 1",
                desc="Body 1",
                members=["dev1"],
                due_date=None,
                status=FakeStatus.TO_DO,
                board_id="board-1",
            ),
            "issue-2": FakeIssue(
                id="issue-2",
                title="Issue 2",
                desc="Body 2",
                members=None,
                due_date="2026-04-15",
                status=FakeStatus.IN_PROGRESS,
                board_id="board-1",
            ),
        }

    def get_boards(self) -> list[FakeBoard]:
        return list(self._boards.values())

    def get_board(self, board_id: str) -> FakeBoard:
        try:
            return self._boards[board_id]
        except KeyError as exc:
            raise BoardNotFoundError(board_id) from exc

    def create_board(self, name: str) -> FakeBoard:
        board = FakeBoard(id="board-3", board_name=name)
        self._boards[board.id] = board
        return board

    def update_board(self, board_id: str, name: str | None = None) -> FakeBoard:
        board = self.get_board(board_id)
        updated = FakeBoard(id=board.id, board_name=name or board.board_name)
        self._boards[board_id] = updated
        return updated

    def delete_board(self, board_id: str) -> bool:
        if board_id not in self._boards:
            raise BoardNotFoundError(board_id)
        del self._boards[board_id]
        return True

    def get_issues(self, board_id: str) -> list[FakeIssue]:
        return [
            issue for issue in self._issues.values() if issue.board_id == board_id
        ]

    def get_issue(self, issue_id: str) -> FakeIssue:
        try:
            return self._issues[issue_id]
        except KeyError as exc:
            raise IssueNotFoundError(issue_id) from exc

    def create_issue(  # noqa: PLR0913
        self,
        title: str,
        board_id: str,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: str | FakeStatus = FakeStatus.TO_DO,
    ) -> FakeIssue:
        issue = FakeIssue(
            id="issue-3",
            title=title,
            desc=desc or "",
            members=members,
            due_date=due_date,
            status=(
                status
                if isinstance(status, FakeStatus)
                else FakeStatus(status)
            ),
            board_id=board_id,
        )
        self._issues[issue.id] = issue
        return issue

    def update_issue(  # noqa: PLR0913
        self,
        issue_id: str,
        title: str | None = None,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: str | FakeStatus | None = None,
        board_id: str | None = None,
    ) -> FakeIssue:
        issue = self.get_issue(issue_id)
        updated = FakeIssue(
            id=issue.id,
            title=title or issue.title,
            desc=desc if desc is not None else issue.desc,
            members=members if members is not None else issue.members,
            due_date=due_date if due_date is not None else issue.due_date,
            status=(
                issue.status
                if status is None
                else status
                if isinstance(status, FakeStatus)
                else FakeStatus(status)
            ),
            board_id=board_id or issue.board_id,
        )
        self._issues[issue_id] = updated
        return updated

    def delete_issue(self, issue_id: str) -> bool:
        if issue_id not in self._issues:
            raise IssueNotFoundError(issue_id)
        del self._issues[issue_id]
        return True


def test_missing_env_returns_500() -> None:
    """Missing env variables returns 500 error."""
    with patch.dict("os.environ", {}, clear=True):
        response = client.get("/boards")

    assert response.status_code == HTTP_INTERNAL_SERVER_ERROR


def test_get_boards_returns_data() -> None:
    """Shared boards endpoint returns expected data."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.get("/boards")

    assert response.status_code == HTTP_OK
    assert len(response.json()) == EXPECTED_BOARD_COUNT


def test_get_board_returns_single_board() -> None:
    """Shared board endpoint returns one board."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.get("/boards/board-1")

    assert response.status_code == HTTP_OK
    assert response.json()["board_name"] == "Platform"


def test_create_board_returns_created_board() -> None:
    """Shared create board endpoint returns created board."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.post("/boards", json={"name": "Infra"})

    assert response.status_code == HTTP_OK
    assert response.json()["board_name"] == "Infra"


def test_update_board_returns_updated_board() -> None:
    """Shared update board endpoint returns updated board."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.patch("/boards/board-1", json={"name": "Platform Eng"})

    assert response.status_code == HTTP_OK
    assert response.json()["board_name"] == "Platform Eng"


def test_delete_board_returns_success() -> None:
    """Shared delete board endpoint returns success."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.delete("/boards/board-1")

    assert response.status_code == HTTP_OK
    assert response.json() == {"success": True}


def test_get_issues_returns_data() -> None:
    """Shared list issues endpoint returns expected data."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.get("/boards/board-1/issues")

    assert response.status_code == HTTP_OK
    assert len(response.json()) == EXPECTED_ISSUE_COUNT


def test_get_issue_returns_single_issue() -> None:
    """Shared issue endpoint returns one issue."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.get("/issues/issue-1")

    assert response.status_code == HTTP_OK
    assert response.json()["id"] == "issue-1"


def test_create_issue_returns_created_issue() -> None:
    """Shared create issue endpoint returns created issue."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.post(
            "/boards/board-1/issues",
            json={"title": "New", "desc": "Body", "status": "completed"},
        )

    assert response.status_code == HTTP_OK
    assert response.json()["title"] == "New"
    assert response.json()["status"] == "completed"


def test_update_issue_returns_updated_issue() -> None:
    """Shared update issue endpoint returns updated issue."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.patch(
            "/issues/issue-1",
            json={"status": "in_progress", "desc": "Updated body"},
        )

    assert response.status_code == HTTP_OK
    assert response.json()["status"] == "in_progress"
    assert response.json()["desc"] == "Updated body"


def test_delete_issue_returns_success() -> None:
    """Shared delete issue endpoint returns success."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.delete("/issues/issue-1")

    assert response.status_code == HTTP_OK
    assert response.json() == {"success": True}


def test_get_issue_returns_404_when_missing() -> None:
    """Shared issue endpoint returns 404 when the issue is missing."""
    with (
        patch.dict("os.environ", SERVICE_ENV),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.get("/issues/missing")

    assert response.status_code == HTTP_NOT_FOUND


def test_get_client_uses_session_token() -> None:
    """Client is built using session token when available."""
    save_session("session-1", "user-trello-token", None, None)

    with patch.dict("os.environ", {"TRELLO_API_KEY": "key"}):
        client_obj = app_module.get_client(session_id="session-1")

    assert isinstance(client_obj, DefaultIssueTrackerClient)


def test_get_client_falls_back_to_env_token() -> None:
    """Client uses env token when no session is provided."""
    with patch.dict(
        "os.environ",
        {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "tok"},
    ):
        client_obj = app_module.get_client(session_id=None)

    assert isinstance(client_obj, DefaultIssueTrackerClient)


def test_root_returns_message() -> None:
    """Root endpoint returns a running message."""
    response = client.get("/")
    assert response.status_code == HTTP_OK
    assert "running" in response.json()["message"].lower()


def test_auth_callback_with_error_returns_400() -> None:
    """Callback with error parameter returns 400."""
    state = create_state()
    response = client.get(
        "/auth/callback",
        params={"state": state, "error": "access_denied"},
    )
    assert response.status_code == HTTP_BAD_REQUEST
