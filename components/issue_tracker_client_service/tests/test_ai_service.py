"""Tests for AI orchestration in the issue tracker service."""

from __future__ import annotations

from issue_tracker_client_service.ai_router import run_ai_chat
from issue_tracker_client_service.ai_schemas import AIChatIn
from starlette import status

HTTP_200_OK = status.HTTP_200_OK


class FakeIssue:
    """Simple fake issue model for tests."""

    def __init__(  # noqa: PLR0913
        self,
        issue_id: str,
        title: str,
        desc: str | None = None,
        status: str | None = None,
        board_id: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
    ) -> None:
        """Initialize a fake issue."""
        self.id = issue_id
        self.title = title
        self.desc = desc
        self.status = status
        self.board_id = board_id
        self.members = members or []
        self.due_date = due_date


class FakeBoard:
    """Simple fake board model for tests."""

    def __init__(self, board_id: str, name: str) -> None:
        """Initialize a fake board."""
        self.id = board_id
        self.name = name


class FakeIssueTrackerClient:
    """Fake issue-tracker client used by AI tests."""

    def get_boards(self) -> list[FakeBoard]:
        """Return fake boards."""
        return [
            FakeBoard(board_id="board-1", name="Platform"),
            FakeBoard(board_id="board-2", name="Backend"),
        ]

    def get_board(self, board_id: str) -> FakeBoard:
        """Return one fake board."""
        return FakeBoard(board_id=board_id, name="Platform")

    def get_issues(self, board_id: str) -> list[FakeIssue]:
        """Return fake issues for a board."""
        return [
            FakeIssue(
                issue_id="issue-1",
                title="Fix login redirect",
                desc="OAuth redirect fails",
                status="to_do",
                board_id=board_id,
            )
        ]

    def get_issue(self, issue_id: str) -> FakeIssue:
        """Return one fake issue."""
        return FakeIssue(
            issue_id=issue_id,
            title="Fix login redirect",
            desc="OAuth redirect fails",
            status="to_do",
            board_id="board-1",
        )

    def create_issue(  # noqa: PLR0913
        self,
        title: str,
        board_id: str,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: object | None = None,
    ) -> FakeIssue:
        """Create and return a fake issue."""
        return FakeIssue(
            issue_id="new-issue-123",
            title=title,
            desc=desc,
            status=str(status) if status is not None else "to_do",
            board_id=board_id,
            members=members,
            due_date=due_date,
        )

    def update_issue(  # noqa: PLR0913
        self,
        issue_id: str,
        title: str | None = None,
        desc: str | None = None,
        members: list[str] | None = None,
        due_date: str | None = None,
        status: object | None = None,
        board_id: str | None = None,
    ) -> FakeIssue:
        """Update and return a fake issue."""
        return FakeIssue(
            issue_id=issue_id,
            title=title or "Updated issue",
            desc=desc,
            status=str(status) if status is not None else "in_progress",
            board_id=board_id or "board-1",
            members=members,
            due_date=due_date,
        )

    def create_board(self, name: str) -> FakeBoard:
        """Create and return a fake board."""
        return FakeBoard(board_id="new-board-123", name=name)

    def update_board(
        self,
        board_id: str,
        name: str | None = None,
    ) -> FakeBoard:
        """Update and return a fake board."""
        return FakeBoard(board_id=board_id, name=name or "Updated board")

    def delete_issue(self, _issue_id: str) -> bool:
        """Delete a fake issue."""
        return True

    def delete_board(self, _board_id: str) -> bool:
        """Delete a fake board."""
        return True


class FakeFunction:
    """Fake tool function payload from an OpenAI tool call."""

    def __init__(self, name: str, arguments: str) -> None:
        """Initialize the fake tool function."""
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    """Fake OpenAI tool call."""

    def __init__(self, tool_id: str, name: str, arguments: str) -> None:
        """Initialize the fake tool call."""
        self.id = tool_id
        self.type = "function"
        self.function = FakeFunction(name=name, arguments=arguments)


class FakeMessage:
    """Fake OpenAI message."""

    def __init__(
        self,
        content: str | None,
        tool_calls: list[FakeToolCall] | None = None,
    ) -> None:
        """Initialize the fake message."""
        self.content = content
        self.tool_calls = tool_calls


class FakeChoice:
    """Fake OpenAI choice wrapper."""

    def __init__(self, message: FakeMessage) -> None:
        """Initialize the fake choice wrapper."""
        self.message = message


class FakeResponse:
    """Fake OpenAI completion response."""

    def __init__(self, message: FakeMessage) -> None:
        """Initialize the fake completion response."""
        self.choices = [FakeChoice(message)]


class FakeCompletions:
    """Fake OpenAI chat completions client."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        """Initialize the fake completions client."""
        self._responses = responses
        self._call_count = 0

    def create(self, **_: object) -> FakeResponse:
        """Return the next fake response in sequence."""
        response = self._responses[self._call_count]
        self._call_count += 1
        return response


class FakeChat:
    """Fake OpenAI chat namespace."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        """Initialize the fake chat namespace with predefined responses."""
        self.completions = FakeCompletions(responses)


class FakeSDKClient:
    """Fake OpenAI SDK client."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        """Initialize the fake SDK client with predefined responses."""
        self.chat = FakeChat(responses)


class FakeAIClient:
    """Fake registered AI client for tests."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        """Initialize the fake AI client with a fake SDK backend."""
        self._client = FakeSDKClient(responses)
        self._model = "fake-model"

    def send_message(
        self,
        _prompt: str,
        _context: dict[str, object] | None = None,
    ) -> str:
        """Return a fallback text response."""
        return "fallback response"


def test_ai_chat_returns_plain_text_when_no_tool_call() -> None:
    """Return plain text when the model does not call a tool."""
    fake_issue_tracker_client = FakeIssueTrackerClient()
    fake_ai_client = FakeAIClient(
        [
            FakeResponse(
                FakeMessage(
                    content="Here is a summary of your issue tracker state.",
                    tool_calls=[],
                )
            )
        ]
    )

    result = run_ai_chat(
        payload=AIChatIn(message="Summarize my issue tracker"),
        issue_tracker_client=fake_issue_tracker_client,
        ai_client=fake_ai_client,
    )

    assert result.reply == "Here is a summary of your issue tracker state."
    assert result.actions == []


def test_ai_chat_can_get_boards() -> None:
    """Execute the get_boards tool and return a final reply."""
    fake_issue_tracker_client = FakeIssueTrackerClient()
    fake_ai_client = FakeAIClient(
        [
            FakeResponse(
                FakeMessage(
                    content=None,
                    tool_calls=[
                        FakeToolCall(
                            tool_id="tool-1",
                            name="get_boards",
                            arguments="{}",
                        )
                    ],
                )
            ),
            FakeResponse(
                FakeMessage(
                    content="You have 2 boards: Platform and Backend.",
                    tool_calls=[],
                )
            ),
        ]
    )

    result = run_ai_chat(
        payload=AIChatIn(message="Show me all boards"),
        issue_tracker_client=fake_issue_tracker_client,
        ai_client=fake_ai_client,
    )

    assert result.reply == "You have 2 boards: Platform and Backend."
    assert len(result.actions) == 1
    assert result.actions[0].tool == "get_boards"
    assert result.actions[0].detail == "Retrieved 2 board(s)."


def test_ai_chat_can_get_issues() -> None:
    """Execute the get_issues tool and return a final reply."""
    fake_issue_tracker_client = FakeIssueTrackerClient()
    fake_ai_client = FakeAIClient(
        [
            FakeResponse(
                FakeMessage(
                    content=None,
                    tool_calls=[
                        FakeToolCall(
                            tool_id="tool-1",
                            name="get_issues",
                            arguments='{"board_id":"board-1"}',
                        )
                    ],
                )
            ),
            FakeResponse(
                FakeMessage(
                    content="Board board-1 has 1 issue.",
                    tool_calls=[],
                )
            ),
        ]
    )

    result = run_ai_chat(
        payload=AIChatIn(message="Show me issues on board-1"),
        issue_tracker_client=fake_issue_tracker_client,
        ai_client=fake_ai_client,
    )

    assert result.reply == "Board board-1 has 1 issue."
    assert len(result.actions) == 1
    assert result.actions[0].tool == "get_issues"
    assert result.actions[0].detail == "Retrieved 1 issue(s) for board board-1."


def test_ai_chat_can_create_issue() -> None:
    """Execute the create_issue tool and return a final reply."""
    fake_issue_tracker_client = FakeIssueTrackerClient()
    fake_ai_client = FakeAIClient(
        [
            FakeResponse(
                FakeMessage(
                    content=None,
                    tool_calls=[
                        FakeToolCall(
                            tool_id="tool-1",
                            name="create_issue",
                            arguments=(
                                '{"title":"OAuth login broken",'
                                '"board_id":"board-1",'
                                '"desc":"Users cannot log in after redirect",'
                                '"status":"to_do"}'
                            ),
                        )
                    ],
                )
            ),
            FakeResponse(
                FakeMessage(
                    content="Created the issue 'OAuth login broken' on board board-1.",
                    tool_calls=[],
                )
            ),
        ]
    )

    result = run_ai_chat(
        payload=AIChatIn(message=(
    "Create a ticket on board-1 called OAuth "
    "login broken"
)
        ),
        issue_tracker_client=fake_issue_tracker_client,
        ai_client=fake_ai_client,
    )

    assert result.reply == "Created the issue 'OAuth login broken' on board board-1."
    assert len(result.actions) == 1
    assert result.actions[0].tool == "create_issue"
    assert result.actions[0].detail == "Created issue 'OAuth login broken' "
    "on board board-1."


def test_ai_chat_can_update_issue() -> None:
    """Execute the update_issue tool and return a final reply."""
    fake_issue_tracker_client = FakeIssueTrackerClient()
    fake_ai_client = FakeAIClient(
        [
            FakeResponse(
                FakeMessage(
                    content=None,
                    tool_calls=[
                        FakeToolCall(
                            tool_id="tool-1",
                            name="update_issue",
                            arguments='{"issue_id":"issue-123","status":"in_progress"}',
                        )
                    ],
                )
            ),
            FakeResponse(
                FakeMessage(
                    content="Moved issue issue-123 to in_progress.",
                    tool_calls=[],
                )
            ),
        ]
    )

    result = run_ai_chat(
        payload=AIChatIn(message="Move issue-123 to in_progress"),
        issue_tracker_client=fake_issue_tracker_client,
        ai_client=fake_ai_client,
    )

    assert result.reply == "Moved issue issue-123 to in_progress."
    assert len(result.actions) == 1
    assert result.actions[0].tool == "update_issue"
    assert result.actions[0].detail == "Updated issue issue-123."


def test_ai_chat_can_create_board() -> None:
    """Execute the create_board tool and return a final reply."""
    fake_issue_tracker_client = FakeIssueTrackerClient()
    fake_ai_client = FakeAIClient(
        [
            FakeResponse(
                FakeMessage(
                    content=None,
                    tool_calls=[
                        FakeToolCall(
                            tool_id="tool-1",
                            name="create_board",
                            arguments='{"name":"Sprint Board"}',
                        )
                    ],
                )
            ),
            FakeResponse(
                FakeMessage(
                    content="Created board Sprint Board.",
                    tool_calls=[],
                )
            ),
        ]
    )

    result = run_ai_chat(
        payload=AIChatIn(message="Create a board called Sprint Board"),
        issue_tracker_client=fake_issue_tracker_client,
        ai_client=fake_ai_client,
    )

    assert result.reply == "Created board Sprint Board."
    assert len(result.actions) == 1
    assert result.actions[0].tool == "create_board"
    assert result.actions[0].detail == "Created board 'Sprint Board'."


def test_ai_chat_can_delete_issue() -> None:
    """Execute the delete_issue tool and return a final reply."""
    fake_issue_tracker_client = FakeIssueTrackerClient()
    fake_ai_client = FakeAIClient(
        [
            FakeResponse(
                FakeMessage(
                    content=None,
                    tool_calls=[
                        FakeToolCall(
                            tool_id="tool-1",
                            name="delete_issue",
                            arguments='{"issue_id":"issue-123"}',
                        )
                    ],
                )
            ),
            FakeResponse(
                FakeMessage(
                    content="Deleted issue issue-123.",
                    tool_calls=[],
                )
            ),
        ]
    )

    result = run_ai_chat(
        payload=AIChatIn(message="Delete issue issue-123"),
        issue_tracker_client=fake_issue_tracker_client,
        ai_client=fake_ai_client,
    )

    assert result.reply == "Deleted issue issue-123."
    assert len(result.actions) == 1
    assert result.actions[0].tool == "delete_issue"
    assert result.actions[0].detail == "Deleted issue issue-123."
