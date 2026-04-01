"""Integration tests — verify DI wiring and client contract.

Tests that importing the implementation registers the factory,
that get_client() returns the correct concrete type, and that
the returned instance satisfies the abstract interface.
"""

import sys
from collections.abc import Generator
from unittest.mock import patch

import issue_tracker_client_api.client as _api
import pytest
from issue_tracker_client_api.client import (
    Issue,
    IssueCreateError,
    IssueListError,
    IssueNotFoundError,
    IssueTrackerClient,
)
from issue_tracker_client_impl.client import DefaultIssueTrackerClient

pytestmark = pytest.mark.integration

HTTP_OK = 200
HTTP_NOT_FOUND = 404

EXPECTED_ISSUE_ID = 1
EXPECTED_COMMENT_ID = 10
EXPECTED_CREATE_ID = 5
EXPECTED_ADD_COMMENT_ID = 42



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

class _FakeIssueState:
    value = "open"


class _FakeIssue:
    def __init__(
        self,
        issue_id: int = EXPECTED_ISSUE_ID,
        title: str = "Test Issue",
        body: str = "Test body",
    ) -> None:
        self.id = issue_id
        self.title = title
        self.body = body
        self.state = _FakeIssueState()


class _FakeComment:
    def __init__(
        self,
        comment_id: int = EXPECTED_COMMENT_ID,
        body: str = "Test comment",
    ) -> None:
        self.id = comment_id
        self.body = body


class _FakeClient:
    """In-memory fake that replaces the Trello client inside the service."""

    def __init__(self, *, api_key: str, token: str) -> None:
        pass

    def list_issues(self, _board: str) -> list[_FakeIssue]:
        return [_FakeIssue()]

    def get_issue(self, _board: str, _issue_id: int) -> _FakeIssue:
        return _FakeIssue(issue_id=_issue_id)

    def create_issue(self, _board: str, title: str, body: str) -> _FakeIssue:
        return _FakeIssue(
            issue_id=EXPECTED_CREATE_ID,
            title=title,
            body=body,
        )

    def close_issue(self, _board: str, _issue_id: int) -> bool:
        return True

    def add_comment(self, _board: str, _issue_id: int, body: str) -> _FakeComment:
        return _FakeComment(comment_id=EXPECTED_ADD_COMMENT_ID, body=body)

class _NotFoundFakeClient:
    """Fake impl that raises a domain not-found error."""

    def __init__(self, *, api_key: str, token: str) -> None:
        pass

    def list_issues(self, _board: str) -> list[_FakeIssue]:
        return [_FakeIssue()]

    def get_issue(self, _board: str, _issue_id: int) -> _FakeIssue:
        msg = "Issue not found"
        raise IssueNotFoundError(msg)

    def create_issue(self, _board: str, title: str, body: str) -> _FakeIssue:
        return _FakeIssue(
            issue_id=EXPECTED_CREATE_ID,
            title=title,
            body=body,
        )

    def close_issue(self, _board: str, _issue_id: int) -> bool:
        return True

    def add_comment(self, _board: str, _issue_id: int, body: str) -> _FakeComment:
        return _FakeComment(comment_id=EXPECTED_ADD_COMMENT_ID, body=body)

class _CreateErrorFakeClient:
    """Fake impl that raises a domain create error."""

    def __init__(self, *, api_key: str, token: str) -> None:
        pass

    def list_issues(self, _board: str) -> list[_FakeIssue]:
        return [_FakeIssue()]

    def get_issue(self, _board: str, issue_id: int) -> _FakeIssue:
        return _FakeIssue(issue_id=issue_id)

    def create_issue(self, _board: str, _title: str, _body: str) -> _FakeIssue:
        msg = "Could not create issue"
        raise IssueCreateError(msg)

    def close_issue(self, _board: str, _issue_id: int) -> bool:
        return True

    def add_comment(self, _board: str, _issue_id: int, body: str) -> _FakeComment:
        return _FakeComment(comment_id=EXPECTED_ADD_COMMENT_ID, body=body)


class _ListErrorFakeClient:
    """Fake impl that raises a domain list error."""

    def __init__(self, *, api_key: str, token: str) -> None:
        pass

    def list_issues(self, _board: str) -> list[_FakeIssue]:
        msg = "Could not list issues"
        raise IssueListError(msg)

    def get_issue(self, _board: str, issue_id: int) -> _FakeIssue:
        return _FakeIssue(issue_id=issue_id)

    def create_issue(self, _board: str, title: str, body: str) -> _FakeIssue:
        return _FakeIssue(
            issue_id=EXPECTED_CREATE_ID,
            title=title,
            body=body,
        )

    def close_issue(self, _board: str, _issue_id: int) -> bool:
        return True

    def add_comment(self, _board: str, _issue_id: int, body: str) -> _FakeComment:
        return _FakeComment(comment_id=EXPECTED_ADD_COMMENT_ID, body=body)


def _build_http_adapter(
    *,
    fake_impl_cls: type[object],
    session_id: str | None = None,
) -> tuple[object, object, object]:
    """Create a real adapter whose generated client talks to the in-process app."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_adapter.adapter import (  # noqa: PLC0415
        ServiceClientAdapter,
    )
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    impl_patcher = patch.object(app_module, "DefaultIssueTrackerClient", fake_impl_cls)
    env_patcher = patch.dict(
        "os.environ",
        {"TRELLO_API_KEY": "k", "TRELLO_API_TOKEN": "t"},
    )

    impl_patcher.start()
    env_patcher.start()

    adapter = ServiceClientAdapter(
        base_url="http://testserver",
        session_id=session_id,
    )
    http_client = TestClient(app, base_url="http://testserver")
    adapter._client.set_httpx_client(http_client)

    return adapter, impl_patcher, env_patcher

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
            return_value=_FakeClient(api_key="k", token="t"), # noqa: S106 - test token
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
    """Adapter over real HTTP translates service 404 into IssueNotFoundError."""
    adapter, impl_patcher, env_patcher = _build_http_adapter(
        fake_impl_cls=_NotFoundFakeClient,
    )
    try:
        with pytest.raises(IssueNotFoundError):
            adapter.get_issue("board", 999)
    finally:
        impl_patcher.stop()
        env_patcher.stop()


def test_adapter_through_service_create_and_comment() -> None:
    """Adapter over real HTTP maps create_issue and add_comment responses."""
    from issue_tracker_client_api.client import Comment  # noqa: PLC0415

    adapter, impl_patcher, env_patcher = _build_http_adapter(
        fake_impl_cls=_FakeClient,
    )
    try:
        issue_result = adapter.create_issue("board", "New", "desc")
        assert isinstance(issue_result, Issue)
        assert issue_result.id == EXPECTED_CREATE_ID
        assert issue_result.title == "New"
        assert issue_result.body == "desc"

        comment_result = adapter.add_comment("board", 1, "hello")
        assert isinstance(comment_result, Comment)
        assert comment_result.id == EXPECTED_ADD_COMMENT_ID
        assert comment_result.body == "hello"
    finally:
        impl_patcher.stop()
        env_patcher.stop()


def test_adapter_full_round_trip_through_service() -> None:
    """Full integration: adapter -> HTTP -> service -> fake client -> domain models."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(
            app_module,
            "DefaultIssueTrackerClient",
            return_value=_FakeClient(api_key="k", token="t"), # noqa: S106 - test token
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
            return_value=_FakeClient(api_key="k", token="t"), # noqa: S106 - test token
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

def test_adapter_over_http_list_issues_error_translates_to_domain_exception() -> None:
    """Service list failure is translated back into a typed domain exception."""
    adapter, impl_patcher, env_patcher = _build_http_adapter(
        fake_impl_cls=_ListErrorFakeClient,
    )
    try:
        with pytest.raises(IssueListError):
            adapter.list_issues("board")
    finally:
        impl_patcher.stop()
        env_patcher.stop()

def test_adapter_over_http_create_issue_error_translates_to_domain_exception() -> None:
    """Service create failure is translated back into a typed domain exception."""
    adapter, impl_patcher, env_patcher = _build_http_adapter(
        fake_impl_cls=_CreateErrorFakeClient,
    )
    try:
        with pytest.raises(IssueCreateError):
            adapter.create_issue("board", "Bad", "Bad body")
    finally:
        impl_patcher.stop()
        env_patcher.stop()

def test_service_http_status_for_not_found() -> None:
    """Service maps domain not-found exception to HTTP 404."""
    from fastapi.testclient import TestClient  # noqa: PLC0415
    from issue_tracker_client_service.app import app  # noqa: PLC0415

    from issue_tracker_client_service import app as app_module  # noqa: PLC0415

    with (
        patch.object(app_module, "DefaultIssueTrackerClient", _NotFoundFakeClient),
        patch.dict("os.environ", {"TRELLO_API_KEY": "k", "TRELLO_API_TOKEN": "t"}),
    ):
        http = TestClient(app)
        response = http.get("/boards/board/issues/999")

    assert response.status_code == HTTP_NOT_FOUND

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
    real_fake = _FakeClient(api_key="k", token="t") # noqa: S106 - test token

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
