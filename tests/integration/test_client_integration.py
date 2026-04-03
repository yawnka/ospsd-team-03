"""Integration tests — verify DI wiring and client contract.

Tests that importing the implementation registers the factory,
that get_client() returns the correct concrete type, and that
the returned instance satisfies the abstract interface.
"""

import sys
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import issue_tracker_client_api.client as _api
import pytest
from issue_tracker_client_api.client import IssueTrackerClient
from issue_tracker_client_impl.client import DefaultIssueTrackerClient

pytestmark = pytest.mark.integration

HTTP_OK = 200


@pytest.fixture(autouse=True)
def _isolate_registry() -> Generator[None, None, None]:
    """Save and restore the global DI registry around each test."""
    saved = list(_api._factories)
    yield
    _api._factories.clear()
    _api._factories.extend(saved)


_FAKE_ENV = {
    "TRELLO_API_KEY": "fake-key",
    "TRELLO_API_TOKEN": "fake-token",
    "ISSUE_TRACKER_SERVICE_URL": "http://localhost:8000",
}


def test_importing_impl_registers_factory() -> None:
    """Importing issue_tracker_client_impl registers a usable factory."""
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)
    import issue_tracker_client_impl  # noqa: PLC0415, F401

    assert _api._factories  # Ensure DI factory was registered before indexing
    factory = _api._factories[0]
    with patch.dict("os.environ", _FAKE_ENV):
        client = factory()

    assert isinstance(client, DefaultIssueTrackerClient)


def _register_impl_only() -> None:
    """Clear factories and register only the impl factory."""
    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_impl", None)
    import issue_tracker_client_impl  # noqa: PLC0415, F401


def test_get_client_returns_concrete_type() -> None:
    """get_client() returns a DefaultIssueTrackerClient instance."""
    _register_impl_only()
    with patch.dict("os.environ", _FAKE_ENV):
        client = _api.get_client()
    assert isinstance(client, DefaultIssueTrackerClient)


def test_get_client_is_subclass_of_interface() -> None:
    """The object returned by get_client() satisfies the abstract contract."""
    _register_impl_only()
    with patch.dict("os.environ", _FAKE_ENV):
        client = _api.get_client()
    assert isinstance(client, IssueTrackerClient)


def test_concrete_client_exposes_interface_methods() -> None:
    """The concrete client has every method declared in the ABC."""
    _register_impl_only()
    with patch.dict("os.environ", _FAKE_ENV):
        client = _api.get_client()
    expected = (
        "list_issues",
        "get_issue",
        "create_issue",
        "close_issue",
        "add_comment",
    )
    for method in expected:
        assert callable(getattr(client, method))


# ---------------------------------------------------------------------------
# Adapter-through-service integration tests
# ---------------------------------------------------------------------------

EXPECTED_ISSUE_ID = 1
EXPECTED_COMMENT_ID = 10
EXPECTED_CREATE_ID = 5
EXPECTED_ADD_COMMENT_ID = 42


class _FakeIssueState:
    value = "open"


class _FakeIssue:
    id = EXPECTED_ISSUE_ID
    title = "Test Issue"
    body = "Test body"
    state = _FakeIssueState()


class _FakeComment:
    id = EXPECTED_COMMENT_ID
    body = "Test comment"


class _FakeClient:
    """In-memory fake that replaces the Trello client inside the service."""

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
        comment = _FakeComment()
        comment.body = body
        return comment


def test_adapter_through_service_list_issues() -> None:
    """ServiceClientAdapter domain mapping works with real service responses."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_adapter.adapter import _to_issue  # noqa: PLC0415
    from issue_tracker_client_api.client import Issue, IssueState  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415
    from issue_tracker_client_service_client.models import IssueOut  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClient(),
        ),
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "k", "TRELLO_API_TOKEN": "t"},
        ),
    ):
        http = TestClient(app)
        resp = http.get("/boards/test-board/issues")

    assert resp.status_code == HTTP_OK
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Issue"

    issue_out = IssueOut(id=1, title="Test Issue", body="Test body", state="open")
    domain_issue = _to_issue(issue_out)
    assert isinstance(domain_issue, Issue)
    assert domain_issue.state == IssueState.OPEN
    assert domain_issue.title == "Test Issue"


def test_adapter_through_service_get_issue() -> None:
    """ServiceClientAdapter raises IssueNotFoundError for missing issues."""
    from issue_tracker_client_adapter.adapter import (  # noqa: PLC0415
        ServiceClientAdapter,
        _to_issue,
    )
    from issue_tracker_client_api.client import (  # noqa: PLC0415
        Issue,
        IssueNotFoundError,
        IssueState,
    )
    from issue_tracker_client_service_client.models import IssueOut  # noqa: PLC0415

    issue_out = IssueOut(id=1, title="Found", body="body", state="open")
    domain = _to_issue(issue_out)
    assert isinstance(domain, Issue)
    assert domain.state == IssueState.OPEN

    adapter = ServiceClientAdapter.__new__(ServiceClientAdapter)
    adapter._session_id = None
    with patch(
        "issue_tracker_client_adapter.adapter"
        ".get_issue_boards_board_issues_issue_id_get.sync",
        return_value=None,
    ):
        adapter._client = MagicMock()
        with pytest.raises(IssueNotFoundError):
            adapter.get_issue("board", 999)


def test_adapter_through_service_create_and_comment() -> None:
    """ServiceClientAdapter correctly maps create_issue and add_comment responses."""
    from issue_tracker_client_adapter.adapter import (  # noqa: PLC0415
        ServiceClientAdapter,
    )
    from issue_tracker_client_api.client import Comment, Issue  # noqa: PLC0415
    from issue_tracker_client_service_client.models import (  # noqa: PLC0415
        CommentOut,
        IssueOut,
    )

    adapter = ServiceClientAdapter.__new__(ServiceClientAdapter)
    adapter._client = MagicMock()
    adapter._session_id = None

    fake_response = IssueOut(
        id=EXPECTED_CREATE_ID, title="New", body="desc", state="open"
    )
    with patch(
        "issue_tracker_client_adapter.adapter"
        ".create_issue_boards_board_issues_post.sync",
        return_value=fake_response,
    ):
        issue_result = adapter.create_issue("board", "New", "desc")
    assert isinstance(issue_result, Issue)
    assert issue_result.id == EXPECTED_CREATE_ID
    assert issue_result.title == "New"

    fake_comment = CommentOut(id=EXPECTED_ADD_COMMENT_ID, body="hello")
    with patch(
        "issue_tracker_client_adapter.adapter"
        ".add_comment_boards_board_issues_issue_id_comments_post.sync",
        return_value=fake_comment,
    ):
        comment_result = adapter.add_comment("board", 1, "hello")
    assert isinstance(comment_result, Comment)
    assert comment_result.id == EXPECTED_ADD_COMMENT_ID
    assert comment_result.body == "hello"


def test_adapter_full_round_trip_through_service() -> None:
    """Full integration: adapter -> HTTP -> service -> fake client -> domain models."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClient(),
        ),
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "k", "TRELLO_API_TOKEN": "t"},
        ),
    ):
        http = TestClient(app)

        # 1. list_issues
        resp = http.get("/boards/b/issues")
        assert resp.status_code == HTTP_OK
        issues = resp.json()
        assert len(issues) == 1

        # 2. get_issue
        resp = http.get("/boards/b/issues/1")
        assert resp.status_code == HTTP_OK
        assert resp.json()["id"] == EXPECTED_ISSUE_ID

        # 3. create_issue
        resp = http.post("/boards/b/issues", json={"title": "T", "body": "B"})
        assert resp.status_code == HTTP_OK
        assert resp.json()["title"] == "T"

        # 4. close_issue
        resp = http.post("/boards/b/issues/1/close")
        assert resp.status_code == HTTP_OK
        assert resp.json()["success"] is True

        # 5. add_comment
        resp = http.post("/boards/b/issues/1/comments", json={"body": "hi"})
        assert resp.status_code == HTTP_OK
        assert resp.json()["body"] == "hi"


def test_adapter_through_generated_client_over_http() -> None:
    """Adapter → generated client → real HTTP → service → fake Trello → domain models.

    This verifies the full adapter integration path: the adapter uses the
    auto-generated client which makes real HTTP calls to the FastAPI service,
    which delegates to a fake Trello client.
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
            return_value=_FakeClient(),
        ),
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "k", "TRELLO_API_TOKEN": "t"},
        ),
    ):
        adapter = ServiceClientAdapter(base_url="http://testserver")
        # Inject TestClient (httpx.Client subclass) as the HTTP transport
        # so generated-client requests reach the in-process ASGI app.
        http_client = TestClient(app, base_url="http://testserver")
        adapter._client.set_httpx_client(http_client)

        # 1. list_issues
        issues = adapter.list_issues("board")
        assert len(issues) == 1
        assert isinstance(issues[0], Issue)
        assert issues[0].state == IssueState.OPEN
        assert issues[0].title == "Test Issue"

        # 2. get_issue
        issue = adapter.get_issue("board", EXPECTED_ISSUE_ID)
        assert isinstance(issue, Issue)
        assert issue.id == EXPECTED_ISSUE_ID
        assert issue.title == "Test Issue"

        # 3. create_issue
        created = adapter.create_issue("board", "New Title", "New Body")
        assert isinstance(created, Issue)
        assert created.title == "New Title"

        # 4. close_issue
        closed = adapter.close_issue("board", EXPECTED_ISSUE_ID)
        assert closed is True

        # 5. add_comment
        comment = adapter.add_comment("board", EXPECTED_ISSUE_ID, "hello")
        assert isinstance(comment, Comment)
        assert comment.body == "hello"


def test_adapter_session_id_forwarded_to_service() -> None:
    """Adapter with session_id uses the session's token instead of env fallback.

    Verifies the full auth path: adapter passes session_id as a per-request
    cookie → service looks up the session → uses the session's access_token
    to build the Trello client.
    """
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_adapter.adapter import (  # noqa: PLC0415
        ServiceClientAdapter,
    )
    from issue_tracker_client_api.client import Issue  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415
    from issue_tracker_client_service.session import save_session  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    # 1. Pre-populate a session in the service's in-memory store
    test_session_id = "integration-test-session"
    save_session(
        test_session_id,
        access_token="session-token-from-oauth",  # noqa: S106 — test credential
        refresh_token=None,
        expires_at=None,
    )

    # 2. Patch DefaultIssueTrackerClient so we can verify which token was used
    captured_tokens: list[str] = []
    real_fake = _FakeClient()

    class _CapturingClient(_FakeClient):
        def __init__(self, *, api_key: str, token: str) -> None:  # noqa: ARG002 — matches real signature
            captured_tokens.append(token)

        def list_issues(self, board: str) -> list[_FakeIssue]:
            return real_fake.list_issues(board)

    with (
        patch.object(app_module, "DefaultIssueTrackerClient", _CapturingClient),
        patch.dict(
            "os.environ",
            {"TRELLO_API_KEY": "k", "TRELLO_API_TOKEN": "env-fallback-token"},
        ),
    ):
        # 3. Create adapter WITH session_id
        adapter = ServiceClientAdapter(
            base_url="http://testserver",
            session_id=test_session_id,
        )
        http_client = TestClient(app, base_url="http://testserver")
        adapter._client.set_httpx_client(http_client)

        issues = adapter.list_issues("board")
        assert isinstance(issues[0], Issue)

    # 4. Verify the service used the session token, not the env fallback
    assert "session-token-from-oauth" in captured_tokens
    assert "env-fallback-token" not in captured_tokens


def test_adapter_di_factory_reads_session_id_env() -> None:
    """DI factory passes ISSUE_TRACKER_SESSION_ID to the adapter."""
    from issue_tracker_client_adapter.adapter import (  # noqa: PLC0415
        ServiceClientAdapter,
    )

    _api._factories.clear()
    sys.modules.pop("issue_tracker_client_adapter", None)

    env = {
        "ISSUE_TRACKER_SERVICE_URL": "http://localhost:8000",
        "ISSUE_TRACKER_SESSION_ID": "my-session",
    }
    with patch.dict("os.environ", env):
        import issue_tracker_client_adapter  # noqa: PLC0415, F401

        client = _api.get_client()

    assert isinstance(client, ServiceClientAdapter)
    assert client._session_id == "my-session"
