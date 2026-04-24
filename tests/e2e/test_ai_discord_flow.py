"""End-to-end HTTP tests across the AI, issue-tracker, and Discord integrations.

Unlike the per-vertical integration tests under ``tests/integration/``, these
drive the full HTTP stack: requests are routed through FastAPI into the AI
orchestrator, which issues tool calls against a fake issue-tracker client,
and — for direct issue creation — triggers the cross-vertical Discord
notification side-effect.

These tests fill two gaps in the existing suite:

1. ``tests/integration/test_client_integration.py`` covers ``/ai/chat`` only
   on the non-tool ``send_message`` fallback path; it does not exercise the
   tool-calling branch over HTTP.
2. ``tests/integration/test_discord_integration.py`` asserts that Discord
   *was* notified, but does not inspect the message content or channel id.

The tests here tighten both, and add a multi-tool orchestration scenario
that demonstrates the AI can chain domain actions in a single turn.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from api.issue import Status as SharedStatus  # type: ignore[import-untyped]
from fastapi.testclient import TestClient
from issue_tracker_client_service.app import app

from issue_tracker_client_service import app as app_module

pytestmark = pytest.mark.e2e

HTTP_OK = 200

_SERVICE_ENV = {
    "TRELLO_API_KEY": "fake-key",
    "TRELLO_API_TOKEN": "fake-token",
    "OPENAI_API_KEY": "fake-openai-key",
}
_DISCORD_ENV = {
    "DISCORD_BOT_TOKEN": "fake-bot",
    "DISCORD_GUILD_ID": "fake-guild",
    "DISCORD_NOTIFY_CHANNEL_ID": "fake-channel",
}


# ─── Fake issue-tracker client ────────────────────────────────────────────


@dataclass
class _FakeIssue:
    id: str
    title: str
    desc: str = ""
    members: list[str] = field(default_factory=list)
    due_date: str | None = None
    status: SharedStatus = SharedStatus.TO_DO
    board_id: str = "board-1"


@dataclass
class _FakeBoard:
    id: str
    board_name: str


class _RecordingTrackerClient:
    """Fake issue-tracker client that records inbound calls for assertions."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get_boards(self) -> list[_FakeBoard]:
        self.calls.append(("get_boards", {}))
        return [_FakeBoard(id="board-1", board_name="Platform")]

    def create_issue(  # noqa: PLR0913
        self,
        title: str,
        board_id: str,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: SharedStatus | str | None = None,
    ) -> _FakeIssue:
        self.calls.append(
            (
                "create_issue",
                {
                    "title": title,
                    "board_id": board_id,
                    "desc": desc,
                    "members": members,
                    "due_date": due_date,
                    "status": status,
                },
            )
        )
        resolved_status: SharedStatus
        if isinstance(status, SharedStatus):
            resolved_status = status
        elif isinstance(status, str):
            resolved_status = SharedStatus(status)
        else:
            resolved_status = SharedStatus.TO_DO

        return _FakeIssue(
            id="new-issue-1",
            title=title,
            desc=desc or "",
            members=members or [],
            due_date=due_date,
            status=resolved_status,
            board_id=board_id,
        )


# ─── Fake OpenAI SDK surface (only the attrs run_ai_chat reaches into) ────


class _FakeFunction:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, tool_id: str, name: str, arguments: str) -> None:
        self.id = tool_id
        self.type = "function"
        self.function = _FakeFunction(name=name, arguments=arguments)


class _FakeSDKMessage:
    def __init__(
        self,
        content: str | None = None,
        tool_calls: list[_FakeToolCall] | None = None,
    ) -> None:
        self.content = content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, message: _FakeSDKMessage) -> None:
        self.message = message


class _FakeResponse:
    def __init__(self, message: _FakeSDKMessage) -> None:
        self.choices = [_FakeChoice(message)]


class _FakeCompletions:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = responses
        self._call_count = 0

    def create(self, **_kwargs: object) -> _FakeResponse:
        response = self._responses[self._call_count]
        self._call_count += 1
        return response


class _FakeChat:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.completions = _FakeCompletions(responses)


class _FakeSDKClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.chat = _FakeChat(responses)


class _FakeAIClient:
    """Fake AI client with the attrs ``run_ai_chat`` needs for tool-calling."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._client = _FakeSDKClient(responses)
        self._model = "fake-model"

    def send_message(
        self,
        _prompt: str,
        _context: dict[str, object] | None = None,
    ) -> str:
        return "fallback response"

    @property
    def client(self) -> _FakeSDKClient:
        return self._client

    @property
    def model(self) -> str:
        return self._model


# ─── Tests ────────────────────────────────────────────────────────────────


def test_ai_chat_http_tool_call_creates_issue_via_tracker() -> None:
    """POST /ai/chat drives the AI through a create_issue tool call.

    Verifies the full HTTP → ai_router → execute_tool → fake tracker round
    trip, plus the model-generated final natural-language reply.
    """
    tracker = _RecordingTrackerClient()
    fake_ai = _FakeAIClient(
        [
            _FakeResponse(
                _FakeSDKMessage(
                    content=None,
                    tool_calls=[
                        _FakeToolCall(
                            tool_id="call-1",
                            name="create_issue",
                            arguments=json.dumps(
                                {
                                    "title": "Fix login",
                                    "board_id": "board-1",
                                    "status": "to_do",
                                }
                            ),
                        )
                    ],
                )
            ),
            _FakeResponse(
                _FakeSDKMessage(content="Created issue 'Fix login' on Platform."),
            ),
        ]
    )

    with (
        patch.dict("os.environ", _SERVICE_ENV, clear=False),
        patch.object(
            app_module, "DefaultIssueTrackerClient", return_value=tracker
        ),
        patch(
            "issue_tracker_client_service.ai_router.get_client",
            return_value=fake_ai,
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/ai/chat",
            json={"message": "Create an issue titled 'Fix login' on board-1"},
        )

    assert response.status_code == HTTP_OK
    body = response.json()
    assert body["reply"] == "Created issue 'Fix login' on Platform."
    assert [action["tool"] for action in body["actions"]] == ["create_issue"]

    tool_call_names = [name for name, _ in tracker.calls]
    assert tool_call_names == ["create_issue"]
    _, kwargs = tracker.calls[0]
    assert kwargs["title"] == "Fix login"
    assert kwargs["board_id"] == "board-1"
    assert kwargs["status"] == SharedStatus.TO_DO


def test_ai_chat_http_multi_tool_orchestration() -> None:
    """AI lists boards, then creates an issue on the returned board.

    Proves multi-tool orchestration works over HTTP and that execute_tool
    dispatches each tool name in the order the model emitted them.
    """
    tracker = _RecordingTrackerClient()
    fake_ai = _FakeAIClient(
        [
            _FakeResponse(
                _FakeSDKMessage(
                    content=None,
                    tool_calls=[
                        _FakeToolCall(
                            tool_id="call-1",
                            name="get_boards",
                            arguments="{}",
                        ),
                        _FakeToolCall(
                            tool_id="call-2",
                            name="create_issue",
                            arguments=json.dumps(
                                {
                                    "title": "Kickoff",
                                    "board_id": "board-1",
                                }
                            ),
                        ),
                    ],
                )
            ),
            _FakeResponse(
                _FakeSDKMessage(
                    content="Listed 1 board and created 'Kickoff'.",
                ),
            ),
        ]
    )

    with (
        patch.dict("os.environ", _SERVICE_ENV, clear=False),
        patch.object(
            app_module, "DefaultIssueTrackerClient", return_value=tracker
        ),
        patch(
            "issue_tracker_client_service.ai_router.get_client",
            return_value=fake_ai,
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/ai/chat",
            json={
                "message": "List boards then create 'Kickoff' on the first one",
            },
        )

    assert response.status_code == HTTP_OK
    body = response.json()
    tool_names = [action["tool"] for action in body["actions"]]
    assert tool_names == ["get_boards", "create_issue"]

    call_names = [name for name, _ in tracker.calls]
    assert call_names == ["get_boards", "create_issue"]


def test_full_vertical_stack_http_issue_create_notifies_discord() -> None:
    """Direct HTTP issue create fires the cross-vertical Discord notification.

    Tightens the happy-path assertion from ``test_discord_integration`` by
    inspecting both the channel id and the message text end-to-end.
    """
    tracker = _RecordingTrackerClient()
    discord_mock = MagicMock()

    with (
        patch.dict("os.environ", {**_SERVICE_ENV, **_DISCORD_ENV}, clear=False),
        patch.object(
            app_module, "DefaultIssueTrackerClient", return_value=tracker
        ),
        patch.object(app_module, "get_chat_client", return_value=discord_mock),
    ):
        client = TestClient(app)
        response = client.post(
            "/boards/board-1/issues",
            json={
                "title": "Ship HW3",
                "desc": "Second submission",
                "status": "to_do",
            },
        )

    assert response.status_code == HTTP_OK

    discord_mock.send_message.assert_called_once()
    kwargs = discord_mock.send_message.call_args.kwargs

    assert kwargs["channel_id"] == "fake-channel"
    assert "Ship HW3" in kwargs["text"]
    assert "board-1" in kwargs["text"]

    assert [name for name, _ in tracker.calls] == ["create_issue"]
