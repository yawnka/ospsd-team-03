"""Integration tests for Discord cross-vertical notification on issue creation."""

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from api.issue import Status as SharedStatus  # type: ignore[import-untyped]
from fastapi.testclient import TestClient
from issue_tracker_client_service.app import app
from issue_tracker_client_service.schemas import IssueOut

from issue_tracker_client_service import app as app_module

pytestmark = pytest.mark.integration

HTTP_OK = 200

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
    """Minimal fake Trello client — only implements create_issue."""

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


def test_notify_discord_called_with_correct_issue_on_create() -> None:
    """Discord notify is called with the IssueOut on successful create."""
    with (
        patch.dict("os.environ", {**_SERVICE_ENV, **_DISCORD_ENV}),
        patch.object(
            app_module, "DefaultIssueTrackerClient", return_value=_FakeTrackerClient()
        ),
        patch.object(app_module, "_notify_discord") as mock_notify,
    ):
        response = client.post(
            "/boards/board-1/issues",
            json={
                "title": "Fix login bug",
                "desc": "Users cannot log in",
                "status": "to_do",
            },
        )

    assert response.status_code == HTTP_OK
    mock_notify.assert_called_once()
    notified_issue: IssueOut = mock_notify.call_args.args[0]
    assert isinstance(notified_issue, IssueOut)
    assert notified_issue.title == "Fix login bug"
    assert notified_issue.board_id == "board-1"
    assert notified_issue.id == "issue-99"


def test_issue_creation_succeeds_when_discord_env_vars_missing() -> None:
    """When Discord env vars are absent, issue creation still returns 200."""
    env_without_discord = {**_SERVICE_ENV}  # no DISCORD_* keys

    with (
        patch.dict("os.environ", env_without_discord, clear=True),
        patch.object(
            app_module, "DefaultIssueTrackerClient", return_value=_FakeTrackerClient()
        ),
    ):
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


def test_issue_creation_succeeds_when_discord_raises() -> None:
    """When Discord send_message raises, issue creation still returns 200."""
    mock_discord = MagicMock()
    mock_discord.send_message.side_effect = RuntimeError("Discord API unavailable")

    with (
        patch.dict("os.environ", {**_SERVICE_ENV, **_DISCORD_ENV}),
        patch.object(
            app_module, "DefaultIssueTrackerClient", return_value=_FakeTrackerClient()
        ),
        patch.object(app_module, "DiscordClient", return_value=mock_discord),
    ):
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
    mock_discord.send_message.assert_called_once()
