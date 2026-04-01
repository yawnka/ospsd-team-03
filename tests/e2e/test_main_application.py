"""End-to-End tests for the ospsd-team-03 application.

This module validates the full application stack as a black box:
file structure, import chains, Python syntax, DI wiring, and
authentication behaviour.
"""

import os
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import issue_tracker_client_api.client as _api
import pytest
import requests
from issue_tracker_client_api.client import IssueTrackerClient
from issue_tracker_client_impl.client import DefaultIssueTrackerClient

# Mark all tests in this file as e2e tests
pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_factories() -> Generator[None, None, None]:
    """Snapshot and restore the DI registry around each E2E test."""
    saved = list(_api._factories)
    yield
    _api._factories.clear()
    _api._factories.extend(saved)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_application_structure_integrity() -> None:
    """All required source files exist in the workspace."""
    expected_files = [
        "pyproject.toml",
        "components/issue_tracker_client_api/pyproject.toml",
        "components/issue_tracker_client_api/src/issue_tracker_client_api/__init__.py",
        "components/issue_tracker_client_api/src/issue_tracker_client_api/client.py",
        "components/issue_tracker_client_impl/pyproject.toml",
        "components/issue_tracker_client_impl/src/issue_tracker_client_impl/__init__.py",
        "components/issue_tracker_client_impl/src/issue_tracker_client_impl/client.py",
        "tests/e2e/test_main_application.py",
    ]

    missing = [f for f in expected_files if not (WORKSPACE_ROOT / f).exists()]

    if missing:
        pytest.fail(f"Missing required files: {missing}")


def test_all_imports_work() -> None:
    """Both packages can be imported in a fresh subprocess."""
    import_test_code = (
        "import issue_tracker_client_api\n"
        "import issue_tracker_client_impl\n"
        'print("All imports successful")\n'
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", import_test_code],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        cwd=str(WORKSPACE_ROOT),
        env={**os.environ, "TRELLO_API_KEY": "dummy"},
    )

    if result.returncode != 0:
        pytest.fail(f"Import check failed:\n{result.stderr}")

    assert "All imports successful" in result.stdout


def test_source_files_syntax_valid() -> None:
    """Every .py file under components/**/src has valid Python syntax."""
    py_files = sorted((WORKSPACE_ROOT / "components").glob("*/src/**/*.py"))

    assert py_files, "No .py files found under components/**/src"

    for py_file in py_files:
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "py_compile", str(py_file)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0:
            pytest.fail(
                f"Syntax error in {py_file.relative_to(WORKSPACE_ROOT)}:\n"
                f"{result.stderr}"
            )


def test_di_full_flow_with_token() -> None:
    """DI round-trip: import -> register -> get_client -> correct type."""
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)

    with patch.dict(
        "os.environ",
        {"TRELLO_API_KEY": "test-key-e2e", "TRELLO_API_TOKEN": "test-token-e2e"},
    ):
        import issue_tracker_client_impl  # noqa: PLC0415, F401

        client = _api.get_client()

    assert isinstance(client, DefaultIssueTrackerClient)


def test_client_raises_without_token() -> None:
    """DefaultIssueTrackerClient raises KeyError when TRELLO_API_KEY is absent."""
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)

    skip = {"TRELLO_API_KEY", "TRELLO_API_TOKEN"}
    env = {k: v for k, v in os.environ.items() if k not in skip}

    with patch.dict("os.environ", env, clear=True):
        import issue_tracker_client_impl  # noqa: PLC0415, F401

        with pytest.raises(KeyError, match="TRELLO_API_KEY"):
            _api.get_client()


def test_location_transparency_impl_wins() -> None:
    """Location transparency: _adapter then _impl → _impl wins.

    Both packages are imported. The last registration (_impl) wins.
    get_client() must return an IssueTrackerClient without any real server connection.
    """
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_adapter", None)
    sys.modules.pop("issue_tracker_client_impl", None)

    env = {
        "ISSUE_TRACKER_SERVICE_URL": "http://fake-service:8000",
        "TRELLO_API_KEY": "fake-key",
        "TRELLO_API_TOKEN": "fake-token",
    }
    with patch.dict("os.environ", env):
        import issue_tracker_client_adapter  # noqa: PLC0415, F401
        import issue_tracker_client_impl  # noqa: PLC0415, F401

        client = _api.get_client()

    assert isinstance(client, IssueTrackerClient)
    assert isinstance(client, DefaultIssueTrackerClient)


def test_location_transparency_adapter_wins() -> None:
    """Location transparency: _impl then _adapter → _adapter wins.

    Both packages are imported. The last registration (_adapter) wins.
    get_client() must return an IssueTrackerClient without any real server connection.
    """
    from issue_tracker_client_adapter.adapter import ServiceClientAdapter  # noqa: I001, PLC0415

    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)
    sys.modules.pop("issue_tracker_client_adapter", None)

    env = {
        "TRELLO_API_KEY": "fake-key",
        "TRELLO_API_TOKEN": "fake-token",
        "ISSUE_TRACKER_SERVICE_URL": "http://fake-service:8000",
    }
    with patch.dict("os.environ", env):
        import issue_tracker_client_impl  # noqa: I001, PLC0415, F401
        import issue_tracker_client_adapter  # noqa: PLC0415, F401

        client = _api.get_client()

    assert isinstance(client, IssueTrackerClient)
    assert isinstance(client, ServiceClientAdapter)


@pytest.mark.local_credentials
def test_full_workflow_against_real_trello() -> None:
    """Full E2E workflow: client creation → API call → response handling."""
    api_key = os.environ.get("TRELLO_API_KEY")
    api_token = os.environ.get("TRELLO_API_TOKEN")
    board_id = os.environ.get("TRELLO_BOARD_ID")

    missing = [
        name
        for name, value in {
            "TRELLO_API_KEY": api_key,
            "TRELLO_API_TOKEN": api_token,
            "TRELLO_BOARD_ID": board_id,
        }.items()
        if not value
    ]
    if missing:
        pytest.skip(
            f"Missing env var(s): {', '.join(missing)} — skipping live E2E test"
        )

    import issue_tracker_client_impl  # noqa: PLC0415, F401

    client = _api.get_client()
    assert isinstance(client, DefaultIssueTrackerClient)

    # 1. list_issues
    issues = client.list_issues(board_id)
    assert isinstance(issues, list)

    # 2. create_issue
    new_issue = client.create_issue(board_id, "E2E Test Card", "Created by E2E test")
    assert new_issue.title == "E2E Test Card"

    # 3. get_issue
    fetched = client.get_issue(board_id, new_issue.id)
    assert fetched.id == new_issue.id
    assert fetched.title == "E2E Test Card"

    # 4. add_comment
    comment = client.add_comment(board_id, new_issue.id, "E2E comment")
    assert comment.body == "E2E comment"

    # 5. close_issue
    result = client.close_issue(board_id, new_issue.id)
    assert result is True


# ---------------------------------------------------------------------------
# Black-box HTTP tests against the running FastAPI service
# ---------------------------------------------------------------------------


class _FakeIssueState:
    value = "open"


class _FakeIssue:
    id = 1
    title = "E2E Issue"
    body = "E2E body"
    state = _FakeIssueState()


class _FakeComment:
    id = 7
    body = "e2e comment"


class _FakeClientForE2E:
    """Fake client injected into the service for black-box HTTP tests."""

    def list_issues(self, _board: str) -> list[_FakeIssue]:
        return [_FakeIssue()]

    def get_issue(self, _board: str, _issue_id: int) -> _FakeIssue:
        return _FakeIssue()

    def create_issue(self, _board: str, title: str, body: str) -> _FakeIssue:
        issue = _FakeIssue()
        issue.title = title
        issue.body = body
        return issue

    def close_issue(self, _board: str, _issue_id: int) -> bool:
        return True

    def add_comment(self, _board: str, _issue_id: int, body: str) -> _FakeComment:
        c = _FakeComment()
        c.body = body
        return c


HTTP_OK = 200
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_REDIRECT = 302
HTTP_BAD_REQUEST = 400

_FAKE_SERVICE_ENV = {"TRELLO_API_KEY": "k", "TRELLO_API_TOKEN": "t"}


def test_service_health_endpoint() -> None:
    """GET /health returns 200 with status ok (black-box HTTP)."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    http = TestClient(app)
    resp = http.get("/health")
    assert resp.status_code == HTTP_OK
    assert resp.json() == {"status": "ok"}


def test_service_root_endpoint() -> None:
    """GET / returns 200 with a running message (black-box HTTP)."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    http = TestClient(app)
    resp = http.get("/")
    assert resp.status_code == HTTP_OK
    assert "running" in resp.json()["message"].lower()


def test_service_list_issues_endpoint() -> None:
    """GET /boards/{board}/issues returns issue list via HTTP."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClientForE2E(),
        ),
        patch.dict("os.environ", _FAKE_SERVICE_ENV),
    ):
        http = TestClient(app)
        resp = http.get("/boards/my-board/issues")

    assert resp.status_code == HTTP_OK
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "E2E Issue"
    assert data[0]["state"] == "open"


def test_service_get_issue_endpoint() -> None:
    """GET /boards/{board}/issues/{id} returns a single issue via HTTP."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClientForE2E(),
        ),
        patch.dict("os.environ", _FAKE_SERVICE_ENV),
    ):
        http = TestClient(app)
        resp = http.get("/boards/my-board/issues/1")

    assert resp.status_code == HTTP_OK
    assert resp.json()["id"] == 1
    assert resp.json()["title"] == "E2E Issue"


def test_service_create_issue_endpoint() -> None:
    """POST /boards/{board}/issues creates an issue via HTTP."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClientForE2E(),
        ),
        patch.dict("os.environ", _FAKE_SERVICE_ENV),
    ):
        http = TestClient(app)
        resp = http.post(
            "/boards/my-board/issues",
            json={"title": "New Issue", "body": "Created via E2E"},
        )

    assert resp.status_code == HTTP_OK
    assert resp.json()["title"] == "New Issue"


def test_service_close_issue_endpoint() -> None:
    """POST /boards/{board}/issues/{id}/close closes an issue via HTTP."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClientForE2E(),
        ),
        patch.dict("os.environ", _FAKE_SERVICE_ENV),
    ):
        http = TestClient(app)
        resp = http.post("/boards/my-board/issues/1/close")

    assert resp.status_code == HTTP_OK
    assert resp.json()["success"] is True


def test_service_add_comment_endpoint() -> None:
    """POST /boards/{board}/issues/{id}/comments adds a comment via HTTP."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClientForE2E(),
        ),
        patch.dict("os.environ", _FAKE_SERVICE_ENV),
    ):
        http = TestClient(app)
        resp = http.post(
            "/boards/my-board/issues/1/comments",
            json={"body": "E2E comment"},
        )

    assert resp.status_code == HTTP_OK
    assert resp.json()["body"] == "E2E comment"


def test_adapter_full_workflow_through_service() -> None:
    """E2E: adapter → generated client → HTTP → service → fake Trello.

    Exercises the complete application stack without requiring real Trello
    credentials: the adapter constructs domain objects from service responses,
    proving location transparency works end-to-end.
    """
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_adapter.adapter import (  # noqa: PLC0415
        ServiceClientAdapter,
    )
    from issue_tracker_client_api.client import (  # noqa: PLC0415
        Comment,
        Issue,
        IssueState,
    )
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClientForE2E(),
        ),
        patch.dict("os.environ", _FAKE_SERVICE_ENV),
    ):
        adapter = ServiceClientAdapter(base_url="http://testserver")
        http_client = TestClient(app, base_url="http://testserver")
        adapter._client.set_httpx_client(http_client)

        # Full workflow: list → get → create → comment → close
        issues = adapter.list_issues("my-board")
        assert len(issues) == 1
        assert isinstance(issues[0], Issue)
        assert issues[0].state == IssueState.OPEN

        issue = adapter.get_issue("my-board", 1)
        assert isinstance(issue, Issue)
        assert issue.title == "E2E Issue"

        created = adapter.create_issue("my-board", "E2E New", "E2E Body")
        assert isinstance(created, Issue)
        assert created.title == "E2E New"

        comment = adapter.add_comment("my-board", 1, "E2E comment")
        assert isinstance(comment, Comment)
        assert comment.body == "E2E comment"

        closed = adapter.close_issue("my-board", 1)
        assert closed is True


def test_service_missing_env_returns_500() -> None:
    """Requests fail with 500 when required env vars are missing."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    with patch.dict("os.environ", {}, clear=True):
        http = TestClient(app)
        resp = http.get("/boards/test/issues")

    assert resp.status_code == HTTP_INTERNAL_SERVER_ERROR

TEST_TRELLO_REDIRECT_URL = "https://trello.com/authorize?oauth_token=test"
TEST_TRELLO_TOKEN = "trello-token-abc" # noqa: S105 - test fixture, not a real secret
TEST_PROD_TOKEN = "prod-token"  # noqa: S105 - test fixture, not a real secret
SUBPROCESS_HEALTH_URL = "http://localhost:8001/health"
SUBPROCESS_PORT = "8001"
REQUEST_TIMEOUT_SECONDS = 5

def test_auth_login_redirects_to_provider() -> None:
    """GET /auth/login redirects user to provider auth URL."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    with (
        patch(
            "issue_tracker_client_service.app.create_state",
            return_value="test-state",
        ),
        patch(
            "issue_tracker_client_service.app.build_authorization_url",
            return_value="https://trello.com/authorize?oauth_token=test",
        ),
    ):
        http = TestClient(app)
        resp = http.get("/auth/login", follow_redirects=False)

    assert resp.status_code == HTTP_REDIRECT
    assert resp.headers["location"] == TEST_TRELLO_REDIRECT_URL


def test_auth_login_invalid_request_returns_400() -> None:
    """GET /auth/login returns 400 for expected auth-start failures."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    with patch(
        "issue_tracker_client_service.app.create_state",
        side_effect=ValueError("bad state"),
    ):
        http = TestClient(app)
        resp = http.get("/auth/login")

    assert resp.status_code == HTTP_BAD_REQUEST
    assert resp.json() == {"detail": "Invalid authorization request"}


def test_auth_login_unexpected_failure_returns_500() -> None:
    """GET /auth/login returns 500 for unexpected startup failures."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    with patch(
        "issue_tracker_client_service.app.build_authorization_url",
        side_effect=RuntimeError("boom"),
    ):
        http = TestClient(app)
        resp = http.get("/auth/login")

    assert resp.status_code == HTTP_INTERNAL_SERVER_ERROR
    assert resp.json() == {"detail": "Failed to start authorization flow"}


def test_auth_token_sets_session_cookie_and_saves_session() -> None:
    """POST /auth/token stores token in session and sets session_id cookie."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    with (
        patch(
            "issue_tracker_client_service.app.secrets.token_urlsafe",
            return_value="session-123",
        ),
        patch("issue_tracker_client_service.app.save_session") as mock_save_session,
        patch.dict("os.environ", {"ENV": "development"}, clear=False),
    ):
        http = TestClient(app)
        resp = http.post("/auth/token", json={"token": TEST_TRELLO_TOKEN})

    assert resp.status_code == HTTP_OK
    assert resp.json() == {
        "status": "authenticated",
        "session_id": "session-123",
    }

    mock_save_session.assert_called_once_with(
        "session-123",
        access_token=TEST_TRELLO_TOKEN,
        refresh_token=None,
        expires_at=None,
    )

    assert resp.cookies.get("session_id") == "session-123"

    set_cookie = resp.headers["set-cookie"].lower()
    assert "session_id=session-123" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "path=/" in set_cookie


def test_auth_token_sets_secure_cookie_in_production() -> None:
    """POST /auth/token marks cookie as Secure in production."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    with (
        patch(
            "issue_tracker_client_service.app.secrets.token_urlsafe",
            return_value="prod-session",
        ),
        patch("issue_tracker_client_service.app.save_session"),
        patch.dict("os.environ", {"ENV": "production"}, clear=False),
    ):
        http = TestClient(app)
        resp = http.post("/auth/token", json={"token": TEST_PROD_TOKEN})

    assert resp.status_code == HTTP_OK
    set_cookie = resp.headers["set-cookie"].lower()
    assert "secure" in set_cookie


def test_auth_callback_returns_html_bridge_page() -> None:
    """GET /auth/callback returns the HTML/JS token bridge page."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    with patch("issue_tracker_client_service.app.consume_state") as mock_consume_state:
        http = TestClient(app)
        resp = http.get("/auth/callback?state=test-state")

    assert resp.status_code == HTTP_OK
    assert "text/html" in resp.headers["content-type"].lower()

    mock_consume_state.assert_called_once_with("test-state")

    body = resp.text
    body_lower = body.lower()

    assert "completing authentication" in body_lower
    assert "window.location.hash" in body
    assert 'params.get("token")' in body
    assert "/auth/token" in body
    assert '"Content-Type": "application/json"' in body
    assert 'JSON.stringify({token: token, state: "test-state"})' in body
    assert "session_id" in body

def test_auth_callback_missing_state_returns_400() -> None:
    """GET /auth/callback returns 400 when state is missing."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    http = TestClient(app)
    resp = http.get("/auth/callback")

    assert resp.status_code == HTTP_BAD_REQUEST
    assert resp.json() == {"detail": "Missing state parameter"}


def test_auth_callback_oauth_error_returns_400() -> None:
    """GET /auth/callback returns 400 when provider sends an error."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    http = TestClient(app)
    resp = http.get("/auth/callback?state=test-state&error=access_denied")

    assert resp.status_code == HTTP_BAD_REQUEST
    assert resp.json() == {"detail": "OAuth error: access_denied"}

def test_service_running_as_process() -> None:
    """True E2E: run service as subprocess and hit it over HTTP."""
    env = {
        **os.environ,
        "TRELLO_API_KEY": "test-key",
        "TRELLO_API_TOKEN": "test-token",
    }

    proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "issue_tracker_client_service.app:app",
            "--port",
            SUBPROCESS_PORT,
        ],
        env=env,
    )

    try:
        time.sleep(2)  # give server time to start

        resp = requests.get(SUBPROCESS_HEALTH_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        assert resp.status_code == HTTP_OK
        assert resp.json() == {"status": "ok"}

    finally:
        proc.terminate()
        proc.wait()


def _same_consumer_code(board_id: str) -> tuple[list[str], str, bool]:
    """Run consumer code using only the abstract API."""
    from issue_tracker_client_api.client import get_client  # noqa: PLC0415

    client = get_client()

    issues = client.list_issues(board_id)
    issue = client.create_issue(board_id, "Same Code", "Same Body")
    closed = client.close_issue(board_id, issue.id)

    return [item.title for item in issues], issue.title, closed


def test_location_transparency_same_consumer_code_both_backends() -> None:
    """E2E: the same consumer code works with impl and adapter unchanged."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_adapter.adapter import (  # noqa: PLC0415
        ServiceClientAdapter,
    )
    from issue_tracker_client_api.client import (  # noqa: PLC0415
        Comment,
        Issue,
        IssueState,
        IssueTrackerClient,
        get_client,
        register,
    )
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    class _LocalImplFake(IssueTrackerClient):
        def list_issues(self, _board: str) -> list[Issue]:
            return [
                Issue(
                    id=1,
                    title="E2E Issue",
                    body="E2E body",
                    state=IssueState.OPEN,
                )
            ]

        def get_issue(self, _board: str, _issue_id: int) -> Issue:
            return Issue(
                id=1,
                title="E2E Issue",
                body="E2E body",
                state=IssueState.OPEN,
            )

        def create_issue(self, _board: str, title: str, body: str) -> Issue:
            return Issue(
                id=1,
                title=title,
                body=body,
                state=IssueState.OPEN,
            )

        def close_issue(self, _board: str, _issue_id: int) -> bool:
            return True

        def add_comment(self, _board: str, _issue_id: int, body: str) -> Comment:
            return Comment(id=7, body=body)

    # First run: local backend
    def make_local_impl() -> IssueTrackerClient:
        return _LocalImplFake()

    register(make_local_impl)

    local_client = get_client()
    assert isinstance(local_client, IssueTrackerClient)

    local_result = _same_consumer_code("my-board")

    # Second run: remote adapter backend
    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClientForE2E(),
        ),
        patch.dict("os.environ", _FAKE_SERVICE_ENV),
    ):
        adapter = ServiceClientAdapter(base_url="http://testserver")
        http_client = TestClient(app, base_url="http://testserver")
        adapter._client.set_httpx_client(http_client)

        def make_adapter() -> IssueTrackerClient:
            return adapter

        register(make_adapter)

        remote_client = get_client()
        assert isinstance(remote_client, IssueTrackerClient)
        assert isinstance(remote_client, ServiceClientAdapter)

        remote_result = _same_consumer_code("my-board")

    assert local_result == remote_result
    assert remote_result == (["E2E Issue"], "Same Code", True)
