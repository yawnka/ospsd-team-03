"""Integration tests for DI wiring across implementation and adapter layers."""

import importlib
import sys
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import issue_tracker_client_api.client as _api
import pytest
from api.client import Client as SharedClient  # type: ignore[import-untyped]
from fastapi.testclient import TestClient
from issue_tracker_client_adapter.adapter import ServiceClientAdapter
from issue_tracker_client_impl.client import DefaultIssueTrackerClient
from issue_tracker_client_service.app import app

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _isolate_registry() -> Generator[None, None, None]:
    """Save and restore the global DI registry around each test."""
    saved = list(_api._factories)
    yield
    _api._factories.clear()
    _api._factories.extend(saved)


_IMPL_ENV = {"TRELLO_API_KEY": "fake-key", "TRELLO_API_TOKEN": "fake-token"}
_ADAPTER_ENV = {"ISSUE_TRACKER_SERVICE_URL": "http://example.test"}


def _reimport_and_register(package_name: str) -> None:
    """Re-import *package_name* so its registration side effect runs again."""
    _api._factories.clear()
    sys.modules.pop(package_name, None)
    importlib.import_module(package_name)
    assert _api._factories


def test_importing_impl_registers_factory() -> None:
    """Importing issue_tracker_client_impl registers a working impl factory."""
    with patch.dict("os.environ", _IMPL_ENV, clear=False):
        _reimport_and_register("issue_tracker_client_impl")
        client = _api.get_client()

    assert callable(_api._factories[0])
    assert isinstance(client, DefaultIssueTrackerClient)


def test_importing_adapter_registers_factory() -> None:
    """Importing issue_tracker_client_adapter registers a working adapter factory."""
    with patch.dict("os.environ", _ADAPTER_ENV, clear=False):
        _reimport_and_register("issue_tracker_client_adapter")
        client = _api.get_client()

    assert callable(_api._factories[0])
    assert isinstance(client, ServiceClientAdapter)


def test_get_client_is_subclass_of_interface() -> None:
    """The impl client returned by get_client() satisfies the shared contract."""
    with patch.dict("os.environ", _IMPL_ENV, clear=False):
        _reimport_and_register("issue_tracker_client_impl")
        client = _api.get_client()

    assert isinstance(client, SharedClient)


@pytest.mark.parametrize(
    ("package_name", "env"),
    [
        ("issue_tracker_client_impl", _IMPL_ENV),
        ("issue_tracker_client_adapter", _ADAPTER_ENV),
    ],
)
def test_registered_client_exposes_interface_methods(
    package_name: str,
    env: dict[str, str],
) -> None:
    """Both registered clients expose the methods declared in the current ABC."""
    with patch.dict("os.environ", env, clear=False):
        _reimport_and_register(package_name)
        client = _api.get_client()

    expected = (
        "get_issue",
        "get_board",
        "get_issues",
        "get_boards",
        "update_issue",
        "update_board",
        "delete_issue",
        "delete_board",
        "create_issue",
        "create_board",
    )
    for method in expected:
        assert callable(getattr(client, method))

HTTP_OK = 200

# Required env vars for the FastAPI lifespan startup validator.
# The ai_client factory also reads OPENAI_API_KEY at registration time.
_STARTUP_ENV = {
    "TRELLO_API_KEY": "fake-key",
    "TRELLO_API_TOKEN": "fake-token",
    "OPENAI_API_KEY": "fake-openai-key",
}


def _set_startup_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Populate the env vars the service requires before accepting requests."""
    for name, value in _STARTUP_ENV.items():
        monkeypatch.setenv(name, value)


def test_ai_chat_plain(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify /ai/chat returns a response using the injected AI client."""
    _set_startup_env(monkeypatch)

    class FakeAIClient:
        def send_message(
            self,
            prompt: str,
            context: dict[str, Any] | None = None,
        ) -> str:
            _ = prompt, context
            return "Hello from AI"

    def fake_get_ai_client() -> FakeAIClient:
        return FakeAIClient()

    monkeypatch.setattr(
        "issue_tracker_client_service.ai_router.get_client",
        fake_get_ai_client,
    )

    with TestClient(app) as client:
        resp = client.post("/ai/chat", json={"message": "hi"})

    assert resp.status_code == HTTP_OK
    assert resp.json() == {"reply": "Hello from AI", "actions": []}


def test_ai_chat_non_tool_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify /ai/chat falls back to send_message when no SDK surface is present.

    The registered AI client lacks ``_client``/``_model``, so ``run_ai_chat``
    must route through ``send_message`` and return the plain text reply with
    an empty actions list.
    """
    _set_startup_env(monkeypatch)

    class FakeAIClient:
        def send_message(
            self,
            prompt: str,
            context: dict[str, Any] | None = None,
        ) -> str:
            _ = prompt, context
            return "listed 0 boards"

    class FakeIssueTracker:
        def get_boards(self) -> list[object]:
            return []

    def fake_get_ai_client() -> FakeAIClient:
        return FakeAIClient()

    def fake_get_issue_tracker() -> FakeIssueTracker:
        return FakeIssueTracker()

    monkeypatch.setattr(
        "issue_tracker_client_service.ai_router.get_client",
        fake_get_ai_client,
    )
    monkeypatch.setattr(
        "issue_tracker_client_service.app.get_client",
        fake_get_issue_tracker,
    )

    with TestClient(app) as client:
        resp = client.post("/ai/chat", json={"message": "list boards"})

    assert resp.status_code == HTTP_OK
    assert resp.json() == {"reply": "listed 0 boards", "actions": []}
