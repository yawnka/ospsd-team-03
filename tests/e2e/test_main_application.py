"""End-to-End tests for the ospsd-team-03 application.

This module validates the full application stack as a black box:
file structure, import chains, Python syntax, DI wiring, and
authentication behaviour.
"""

import os
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import issue_tracker_client_api.client as _api
import pytest
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


def test_service_missing_env_returns_500() -> None:
    """Requests fail with 500 when required env vars are missing."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    with patch.dict("os.environ", {}, clear=True):
        http = TestClient(app)
        resp = http.get("/boards/test/issues")

    assert resp.status_code == HTTP_INTERNAL_SERVER_ERROR
