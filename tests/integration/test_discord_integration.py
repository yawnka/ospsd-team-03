"""Integration tests for Discord cross-vertical notification on issue creation."""

import json
from dataclasses import dataclass

import pytest
from api.issue import Status as SharedStatus  # type: ignore[import-untyped]
from fastapi.testclient import TestClient
from issue_tracker_client_service.app import app

from issue_tracker_client_service import app as app_module

pytestmark = pytest.mark.integration

HTTP_OK = 200
MIN_AI_DISCORD_MESSAGES = 2

_SERVICE_ENV = {
    "TRELLO_API_KEY": "fake-key",
    "TRELLO_API_TOKEN": "fake-token",
}
_DISCORD_ENV = {
    "DISCORD_BOT_TOKEN": "fake-bot-token",
    "DISCORD_GUILD_ID": "fake-guild-id",
    "DISCORD_NOTIFY_CHANNEL_ID": "fake-channel-id",
}

client = TestClient(app)


@dataclass
class _FakeIssue:
    id: str
    title: str
    desc: str
    members: list[str] | None
    due_date: str | None
    status: SharedStatus
    board_id: str


class _FakeTrackerClient:
    """Minimal fake Trello client that implements issue creation."""

    def create_issue(  # noqa: PLR0913
        self,
        title: str,
        board_id: str,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: SharedStatus | str = SharedStatus.TO_DO,
    ) -> _FakeIssue:
        return _FakeIssue(
            id="issue-99",
            title=title,
            desc=desc or "",
            members=members,
            due_date=due_date,
            status=status if isinstance(status, SharedStatus) else SharedStatus(status),
            board_id=board_id,
        )


class _RecordingTrackerClient(_FakeTrackerClient):
    """Fake tracker client that records created issues for assertions."""

    def __init__(self) -> None:
        self.created_issues: list[_FakeIssue] = []

    def create_issue(  # noqa: PLR0913
        self,
        title: str,
        board_id: str,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: SharedStatus | str = SharedStatus.TO_DO,
    ) -> _FakeIssue:
        issue = super().create_issue(
            title=title,
            board_id=board_id,
            desc=desc,
            members=members,
            due_date=due_date,
            status=status,
        )
        self.created_issues.append(issue)
        return issue


class _RecordingChatClient:
    """Fake shared chat client that records sent messages."""

    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str]] = []

    def send_message(self, *, channel_id: str, text: str) -> object:
        self.sent_messages.append(
            {
                "channel_id": channel_id,
                "text": text,
            }
        )
        return object()


class _FailingChatClient:
    """Fake shared chat client that simulates Discord failure."""

    def __init__(self) -> None:
        self.send_attempts = 0

    def send_message(self, *, channel_id: str, text: str) -> object:
        del channel_id, text

        self.send_attempts += 1
        msg = "Discord API unavailable"
        raise RuntimeError(msg)

@dataclass
class _FakeFunction:
    name: str
    arguments: str


@dataclass
class _FakeToolCall:
    id: str
    type: str
    function: _FakeFunction


@dataclass
class _FakeMessage:
    content: str | None
    tool_calls: list[_FakeToolCall] | None = None


@dataclass
class _FakeChoice:
    message: _FakeMessage


@dataclass
class _FakeResponse:
    choices: list[_FakeChoice]


class _FakeAIClient:
    """Fake AI client that returns deterministic chat-completion responses."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = responses
        self.calls: list[dict[str, object]] = []

    def create_chat_completion(self, **kwargs: object) -> _FakeResponse:
        self.calls.append(kwargs)
        return self._responses.pop(0)


def _set_env(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]) -> None:
    for key, value in env.items():
        monkeypatch.setenv(key, value)


def _clear_discord_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _DISCORD_ENV:
        monkeypatch.delenv(key, raising=False)

def _tracker_factory(tracker: _FakeTrackerClient) -> object:
    def create_tracker(api_key: str, token: str) -> _FakeTrackerClient:
        del api_key, token
        return tracker

    return create_tracker


def test_notify_chat_called_with_correct_issue_on_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chat notify is called on successful issue create."""
    notifications: list[tuple[str, str]] = []

    def record_notification(action: str, detail: str) -> None:
        notifications.append((action, detail))

    _set_env(monkeypatch, {**_SERVICE_ENV, **_DISCORD_ENV})
    monkeypatch.setattr(
        app_module,
        "DefaultIssueTrackerClient",
        _tracker_factory(_FakeTrackerClient()),
    )
    monkeypatch.setattr(app_module, "_notify_chat_action", record_notification)

    response = client.post(
        "/boards/board-1/issues",
        json={
            "title": "Fix login bug",
            "desc": "Users cannot log in",
            "status": "to_do",
        },
    )

    assert response.status_code == HTTP_OK
    assert len(notifications) == 1

    action, detail = notifications[0]
    assert action == "New issue created"
    assert "Fix login bug" in detail
    assert "board-1" in detail


def test_issue_creation_succeeds_when_discord_env_vars_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Discord env vars are absent, issue creation still returns 200."""
    _set_env(monkeypatch, _SERVICE_ENV)
    _clear_discord_env(monkeypatch)
    monkeypatch.setattr(
        app_module,
        "DefaultIssueTrackerClient",
        _tracker_factory(_FakeTrackerClient()),
    )

    response = client.post(
        "/boards/board-1/issues",
        json={
            "title": "Add dark mode",
            "desc": "Feature request",
            "status": "to_do",
        },
    )

    assert response.status_code == HTTP_OK
    assert response.json()["title"] == "Add dark mode"


def test_issue_creation_succeeds_when_discord_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Discord send_message raises, issue creation still returns 200."""
    failing_chat = _FailingChatClient()

    _set_env(monkeypatch, {**_SERVICE_ENV, **_DISCORD_ENV})
    monkeypatch.setattr(
        app_module,
        "DefaultIssueTrackerClient",
        _tracker_factory(_FakeTrackerClient()),
    )
    monkeypatch.setattr(app_module, "get_chat_client", lambda: failing_chat)

    response = client.post(
        "/boards/board-1/issues",
        json={
            "title": "Improve search",
            "desc": "Search is slow",
            "status": "to_do",
        },
    )

    assert response.status_code == HTTP_OK
    assert response.json()["title"] == "Improve search"
    assert failing_chat.send_attempts == 1


def test_ai_chat_returns_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    """AI chat endpoint returns the final AI reply through real route code."""
    fake_ai = _FakeAIClient(
        responses=[
            _FakeResponse(
                choices=[
                    _FakeChoice(
                        message=_FakeMessage(
                            content="There is one board available.",
                            tool_calls=None,
                        )
                    )
                ]
            )
        ]
    )

    _set_env(
        monkeypatch,
        {
            **_SERVICE_ENV,
            **_DISCORD_ENV,
            "OPENAI_API_KEY": "fake-openai-key",
        },
    )
    monkeypatch.setattr(
        app_module,
        "DefaultIssueTrackerClient",
        _tracker_factory(_FakeTrackerClient()),
    )
    monkeypatch.setattr(
        "issue_tracker_client_service.ai_router.get_client",
        lambda: fake_ai,
    )

    response = client.post(
        "/ai/chat",
        json={"message": "list boards"},
    )

    assert response.status_code == HTTP_OK
    assert response.json()["reply"] == "There is one board available."
    assert len(fake_ai.calls) == 1


def test_ai_tool_call_create_issue_notifies_discord(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AI tool call creates an issue and notifies Discord.

    This tests:
    /ai/chat -> AI create_issue tool call -> issue tracker action ->
    shared chat/Discord notification.

    External network providers are replaced with deterministic fakes so CI does
    not require OpenAI, Trello, or Discord credentials. The FastAPI route, AI
    tool-call executor, issue creation dispatch, and Discord notification hook
    are real application code.
    """
    tracker = _RecordingTrackerClient()
    chat = _RecordingChatClient()
    fake_ai = _FakeAIClient(
        responses=[
            _FakeResponse(
                choices=[
                    _FakeChoice(
                        message=_FakeMessage(
                            content=None,
                            tool_calls=[
                                _FakeToolCall(
                                    id="call-1",
                                    type="function",
                                    function=_FakeFunction(
                                        name="create_issue",
                                        arguments=json.dumps(
                                            {
                                                "title": "Fix OAuth callback",
                                                "board_id": "board-1",
                                                "desc": "Callback loses token state",
                                                "status": "to_do",
                                            }
                                        ),
                                    ),
                                )
                            ],
                        )
                    )
                ]
            ),
            _FakeResponse(
                choices=[
                    _FakeChoice(
                        message=_FakeMessage(
                            content=(
                                "Created issue 'Fix OAuth callback' "
                                "and notified Discord."
                            ),
                            tool_calls=None,
                        )
                    )
                ]
            ),
        ]
    )

    _set_env(
        monkeypatch,
        {
            **_SERVICE_ENV,
            **_DISCORD_ENV,
            "OPENAI_API_KEY": "fake-openai-key",
        },
    )
    monkeypatch.setattr(
        app_module,
        "DefaultIssueTrackerClient",
        _tracker_factory(tracker),
    )
    monkeypatch.setattr(
        "issue_tracker_client_service.ai_router.get_client",
        lambda: fake_ai,
    )
    monkeypatch.setattr(app_module, "get_chat_client", lambda: chat)

    response = client.post(
        "/ai/chat",
        json={
            "message": (
                "Create an issue titled 'Fix OAuth callback' on board-1 "
                "and notify Discord."
            ),
        },
    )

    assert response.status_code == HTTP_OK

    body = response.json()
    assert body["reply"] == "Created issue 'Fix OAuth callback' and notified Discord."
    assert [action["tool"] for action in body["actions"]] == ["create_issue"]

    assert len(tracker.created_issues) == 1
    created_issue = tracker.created_issues[0]
    assert created_issue.title == "Fix OAuth callback"
    assert created_issue.board_id == "board-1"
    assert created_issue.desc == "Callback loses token state"
    assert created_issue.status == SharedStatus.TO_DO

    assert len(chat.sent_messages) >= MIN_AI_DISCORD_MESSAGES

    sent_messages = [message["text"] for message in chat.sent_messages]
    sent_channels = [message["channel_id"] for message in chat.sent_messages]

    assert all(channel == "fake-channel-id" for channel in sent_channels)
    assert any("AI executed `create_issue`" in message for message in sent_messages)
    assert any("Fix OAuth callback" in message for message in sent_messages)
    assert any("AI response:" in message for message in sent_messages)
