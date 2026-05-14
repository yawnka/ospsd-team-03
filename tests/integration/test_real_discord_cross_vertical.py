"""Credential-gated cross-vertical integration test with real Discord.

This module exists to satisfy the HW3 rubric requirement that at least one
integration test exercise real cross-vertical behavior instead of mocking every
component. It keeps OpenAI and Trello deterministic, but deliberately uses the
published Chat vertical API plus Team 8's Discord implementation to send to a
sandbox Discord channel.
"""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from api.issue import Status as SharedStatus  # type: ignore[import-untyped]
from chat_client_api import (  # type: ignore[import-untyped]
    get_client as get_real_chat_client,
)
from fastapi.testclient import TestClient
from issue_tracker_client_service.app import app

from issue_tracker_client_service import app as app_module

pytestmark = [pytest.mark.integration, pytest.mark.local_credentials]

HTTP_OK = 200
_REQUIRED_DISCORD_ENV = (
    "DISCORD_BOT_TOKEN",
    "DISCORD_GUILD_ID",
    "DISCORD_NOTIFY_CHANNEL_ID",
)
_SERVICE_ENV = {
    "TRELLO_API_KEY": "fake-key",
    "TRELLO_API_TOKEN": "fake-token",
    "OPENAI_API_KEY": "fake-openai-key",
}


@dataclass
class _FakeIssue:
    id: str
    title: str
    desc: str = ""
    members: list[str] = field(default_factory=list)
    due_date: str | None = None
    status: SharedStatus = SharedStatus.TO_DO
    board_id: str = "board-1"


class _RecordingTrackerClient:
    """Deterministic issue tracker used so the only network dependency is Discord."""

    def __init__(self) -> None:
        self.created_issues: list[_FakeIssue] = []

    def create_issue(  # noqa: PLR0913
        self,
        title: str,
        board_id: str,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: SharedStatus | str | None = None,
    ) -> _FakeIssue:
        resolved_status = (
            status
            if isinstance(status, SharedStatus)
            else SharedStatus(status or SharedStatus.TO_DO.value)
        )
        issue = _FakeIssue(
            id="sandbox-issue-1",
            title=title,
            desc=desc or "",
            members=members or [],
            due_date=due_date,
            status=resolved_status,
            board_id=board_id,
        )
        self.created_issues.append(issue)
        return issue


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


class _FakeAIClient:
    """Fake AI client that emits one create_issue tool call, then a final reply."""

    def __init__(self, marker: str) -> None:
        self._responses = [
            _FakeResponse(
                _FakeSDKMessage(
                    tool_calls=[
                        _FakeToolCall(
                            tool_id="call-1",
                            name="create_issue",
                            arguments=json.dumps(
                                {
                                    "title": f"Discord sandbox issue {marker}",
                                    "board_id": "board-1",
                                    "desc": "Created by real Discord integration test",
                                    "status": "to_do",
                                }
                            ),
                        )
                    ]
                )
            ),
            _FakeResponse(
                _FakeSDKMessage(
                    content=f"Created sandbox issue and notified Discord: {marker}"
                )
            ),
        ]
        self._call_count = 0

    def send_message(
        self,
        _prompt: str,
        _context: dict[str, object] | None = None,
    ) -> str:
        return "fallback response"

    def create_chat_completion(
        self,
        messages: list[dict[str, object]],
        tools: list[dict[str, object]] | None = None,
        tool_choice: str | None = None,
    ) -> _FakeResponse:
        del messages, tools, tool_choice

        response = self._responses[self._call_count]
        self._call_count += 1
        return response


def _require_real_discord_env() -> None:
    if os.getenv("DISCORD_INTEGRATION_TESTS") != "1":
        pytest.skip("Set DISCORD_INTEGRATION_TESTS=1 to run real Discord test")

    missing = [name for name in _REQUIRED_DISCORD_ENV if not os.getenv(name)]
    if missing:
        pytest.skip(f"Missing real Discord env vars: {', '.join(missing)}")


def test_ai_tool_call_sends_real_discord_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run AI tool-call -> issue action -> real Discord send via shared API.

    OpenAI and Trello are controlled test doubles so this remains deterministic.
    The Chat vertical is not mocked: importing ``discord_client_impl`` registers
    Team 8's provider with ``chat_client_api.get_client()``, and the service's
    normal notification hook sends to the sandbox channel through Discord HTTP.
    """
    _require_real_discord_env()

    importlib.import_module("discord_client_impl")

    marker = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    tracker = _RecordingTrackerClient()
    fake_ai = _FakeAIClient(marker=marker)

    for key, value in _SERVICE_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("CHAT_CLIENT_IMPL_MODULE", "discord_client_impl")

    monkeypatch.setattr(app_module, "DefaultIssueTrackerClient", lambda **_: tracker)
    monkeypatch.setattr(
        "issue_tracker_client_service.ai_router.get_client",
        lambda: fake_ai,
    )

    client = TestClient(app)
    response = client.post(
        "/ai/chat",
        json={"message": f"Create a Discord sandbox issue {marker}"},
    )

    assert response.status_code == HTTP_OK
    body = response.json()
    assert body["reply"] == f"Created sandbox issue and notified Discord: {marker}"
    assert [action["tool"] for action in body["actions"]] == ["create_issue"]

    assert len(tracker.created_issues) == 1
    assert tracker.created_issues[0].title == f"Discord sandbox issue {marker}"

    chat_client = get_real_chat_client()
    channel_id = os.environ["DISCORD_NOTIFY_CHANNEL_ID"]
    recent_messages: list[Any] = chat_client.get_messages(
        channel_id=channel_id,
        limit=10,
    )
    recent_text = "\n".join(str(message.text) for message in recent_messages)

    assert marker in recent_text
    assert "AI executed `create_issue`" in recent_text
