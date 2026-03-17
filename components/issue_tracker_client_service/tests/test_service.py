"""Unit tests for the issue tracker client service."""

import time
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
HTTP_INTERNAL_SERVER_ERROR = 500

EXPECTED_ISSUE_COUNT = 2
EXPECTED_ACCESS_TOKEN = "test-access-token"  # noqa: S105 — test constant
EXPECTED_REFRESH_TOKEN = "test-refresh-token"  # noqa: S105 — test constant
OLD_ACCESS_TOKEN = "old-access-token"  # noqa: S105 - test constant
NEW_ACCESS_TOKEN = "new-access-token"  # noqa: S105 - test constant
TEST_REFRESH_TOKEN = "test-refresh-token"  # noqa: S105 - test constant

# Create a TestClient instance for making requests
client = TestClient(app)


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------

def test_health() -> None:
    """Health endpoint returns OK."""
    response = client.get("/health")

    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "ok"}


# -----------------------------------------------------------------------------
# Auth
# -----------------------------------------------------------------------------

def test_create_and_consume_state() -> None:
    """Create and consume a valid OAuth state."""
    state = create_state()
    consume_state(state)


def test_consume_invalid_state_raises() -> None:
    """Invalid state raises an exception."""
    with pytest.raises(Exception, match="Invalid OAuth state"):
        consume_state("invalid-state")


def test_auth_login_redirects() -> None:
    """Login endpoint redirects to auth provider."""
    with patch.object(
        app_module,
        "build_authorization_url",
        return_value="https://example.com/auth?state=abc",
    ):
        response = client.get("/auth/login", follow_redirects=False)

    assert response.status_code == HTTP_FOUND
    assert "https://example.com/auth" in response.headers["location"]


def test_auth_callback_sets_session_cookie() -> None:
    """Callback exchanges code and sets session cookie."""
    state = create_state()

    with patch.object(
        app_module,
        "exchange_code_for_token",
        return_value={
            "access_token": EXPECTED_ACCESS_TOKEN,
            "refresh_token": EXPECTED_REFRESH_TOKEN,
        },
    ):
        response = client.get(
            "/auth/callback",
            params={"code": "abc", "state": state},
        )

    assert response.status_code == HTTP_OK
    assert response.json() == {"status": "authenticated"}

    session_id = response.cookies.get("session_id")
    assert session_id is not None

    session = get_session(session_id)
    assert session is not None
    assert session.access_token == EXPECTED_ACCESS_TOKEN
    assert session.refresh_token == EXPECTED_REFRESH_TOKEN
    assert session.expires_at is not None


# -----------------------------------------------------------------------------
# Fake client
# -----------------------------------------------------------------------------

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
        return [
            FakeIssue(1, "Issue 1", "Body 1", FakeIssueState.OPEN),
            FakeIssue(2, "Issue 2", "Body 2", FakeIssueState.CLOSED),
        ]

    def get_issue(self, _board: str, _issue_id: int) -> FakeIssue:
        return FakeIssue(1, "Issue 1", "Body 1", FakeIssueState.OPEN)

    def create_issue(self, _board: str, title: str, body: str) -> FakeIssue:
        return FakeIssue(3, title, body, FakeIssueState.OPEN)

    def close_issue(self, _board: str, _issue_id: int) -> bool:
        return True

    def add_comment(self, _board: str, _issue_id: int, body: str) -> FakeComment:
        return FakeComment(10, body)


# -----------------------------------------------------------------------------
# Issue endpoints
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Session/Refresh
# -----------------------------------------------------------------------------

def test_get_client_refreshes_expired_token() -> None:
    """Expired session refreshes the access token."""
    expired_time = time.time() - 10
    save_session(
        "session-1",
        OLD_ACCESS_TOKEN,
        TEST_REFRESH_TOKEN,
        expired_time,
    )

    with (
        patch.object(
            app_module,
            "refresh_access_token",
            return_value={"access_token": NEW_ACCESS_TOKEN, "expires_in": 3600},
        ),
        patch.dict("os.environ", {"TRELLO_API_KEY": "key"}),
    ):
        client_obj = app_module.get_client(session_id="session-1")

    session = get_session("session-1")
    assert session is not None
    assert session.access_token == NEW_ACCESS_TOKEN
    assert session.expires_at is not None
    assert isinstance(client_obj, DefaultIssueTrackerClient)
