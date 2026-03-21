"""Unit tests for the issue tracker client service."""

from dataclasses import dataclass
from enum import Enum
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from issue_tracker_client_impl.client import DefaultIssueTrackerClient
from issue_tracker_client_service.app import app
from issue_tracker_client_service.auth import consume_state, create_state
from issue_tracker_client_service.session import get_session, save_session

from issue_tracker_client_service import app as app_module

pytestmark = pytest.mark.unit

HTTP_OK = 200
HTTP_FOUND = 302
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_SERVER_ERROR = 500

EXPECTED_ISSUE_COUNT = 2

# Create a TestClient instance for making requests
client = TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health() -> None:
    """Health endpoint returns OK."""
    response = client.get("/health")

    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


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
    assert session.access_token == "trello-user-token"  # noqa: S105 — test credential


def test_auth_token_missing_token_returns_400() -> None:
    """Token endpoint without token returns 400."""
    response = client.post("/auth/token", json={})
    assert response.status_code == HTTP_BAD_REQUEST


# ---------------------------------------------------------------------------
# Fake client
# ---------------------------------------------------------------------------


class FakeIssueState(Enum):
    """Fake issue states."""

    OPEN = "open"
    CLOSED = "closed"


@dataclass
class FakeIssue:
    """Fake issue model."""

    id: int
    title: str
    body: str
    state: FakeIssueState


@dataclass
class FakeComment:
    """Fake comment model."""

    id: int
    body: str


class FakeClient:
    """Fake client for endpoint tests."""

    def list_issues(self, _board: str) -> list[FakeIssue]:
        """Return fake issues."""
        return [
            FakeIssue(1, "Issue 1", "Body 1", FakeIssueState.OPEN),
            FakeIssue(2, "Issue 2", "Body 2", FakeIssueState.CLOSED),
        ]

    def get_issue(self, _board: str, _issue_id: int) -> FakeIssue:
        """Return a fake issue."""
        return FakeIssue(1, "Issue 1", "Body 1", FakeIssueState.OPEN)

    def create_issue(self, _board: str, title: str, body: str) -> FakeIssue:
        """Return a fake created issue."""
        return FakeIssue(3, title, body, FakeIssueState.OPEN)

    def close_issue(self, _board: str, _issue_id: int) -> bool:
        """Return success."""
        return True

    def add_comment(self, _board: str, _issue_id: int, body: str) -> FakeComment:
        """Return a fake comment."""
        return FakeComment(10, body)


# ---------------------------------------------------------------------------
# Issue endpoints
# ---------------------------------------------------------------------------


def test_missing_env_returns_500() -> None:
    """Missing env variables returns 500 error."""
    with patch.dict("os.environ", {}, clear=True):
        response = client.get("/boards/test/issues")

    assert response.status_code == HTTP_INTERNAL_SERVER_ERROR


def test_list_issues_returns_data() -> None:
    """List issues endpoint returns expected data."""
    with (
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        ),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.get("/boards/test/issues")

    assert response.status_code == HTTP_OK
    assert len(response.json()) == EXPECTED_ISSUE_COUNT


def test_get_issue_returns_single_issue() -> None:
    """Get issue endpoint returns one issue."""
    with (
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        ),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.get("/boards/test/issues/1")

    assert response.status_code == HTTP_OK
    assert response.json()["id"] == 1


def test_create_issue_returns_created_issue() -> None:
    """Create issue endpoint returns created issue."""
    with (
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        ),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.post(
            "/boards/test/issues",
            json={"title": "New", "body": "Body"},
        )

    assert response.status_code == HTTP_OK
    assert response.json()["title"] == "New"


def test_close_issue_returns_success() -> None:
    """Close issue endpoint returns success."""
    with (
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        ),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.post("/boards/test/issues/1/close")

    assert response.status_code == HTTP_OK
    assert response.json() == {"success": True}


def test_add_comment_returns_comment() -> None:
    """Add comment endpoint returns created comment."""
    with (
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        ),
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=FakeClient(),
        ),
    ):
        response = client.post(
            "/boards/test/issues/1/comments",
            json={"body": "Nice"},
        )

    assert response.status_code == HTTP_OK
    assert response.json() == {"id": 10, "body": "Nice"}


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


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
