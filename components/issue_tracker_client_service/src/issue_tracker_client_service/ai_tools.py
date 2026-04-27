"""AI tool definitions and execution helpers for the issue tracker service."""

from __future__ import annotations

import json
from typing import Any

from api.client import Client  # noqa: TC002
from api.issue import Status

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_boards",
            "description": "List all available boards.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_board",
            "description": "Get a single board by board_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The board ID.",
                    },
                },
                "required": ["board_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_issues",
            "description": "List all issues for a specific board.",
            "parameters": {
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The board ID.",
                    },
                },
                "required": ["board_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_issue",
            "description": "Get a single issue by issue_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "The issue ID.",
                    },
                },
                "required": ["issue_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_issue",
            "description": "Create a new issue on a board.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The issue title.",
                    },
                    "board_id": {
                        "type": "string",
                        "description": "The board ID.",
                    },
                    "desc": {
                        "type": "string",
                        "description": "Optional issue description.",
                    },
                    "members": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of member IDs.",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Optional due date string.",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["to_do", "in_progress", "completed"],
                        "description": "Optional issue status.",
                    },
                },
                "required": ["title", "board_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_issue",
            "description": "Update an existing issue. Use this to change "
            "title, description, members, due date, status, or board.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "The issue ID.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional new title.",
                    },
                    "desc": {
                        "type": "string",
                        "description": "Optional new description.",
                    },
                    "members": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional new member IDs.",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Optional new due date string.",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["to_do", "in_progress", "completed"],
                        "description": "Optional new issue status.",
                    },
                    "board_id": {
                        "type": "string",
                        "description": "Optional new board ID.",
                    },
                },
                "required": ["issue_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_board",
            "description": "Create a new board.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Board name.",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_board",
            "description": "Update a board name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "Board ID.",
                    },
                    "name": {
                        "type": "string",
                        "description": "New board name.",
                    },
                },
                "required": ["board_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_issue",
            "description": "Delete an issue by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "Issue ID.",
                    },
                },
                "required": ["issue_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_board",
            "description": "Delete a board by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "Board ID.",
                    },
                },
                "required": ["board_id"],
            },
        },
    },
]


def _parse_status(value: str | None) -> Status | None:
    """Convert a string status into the shared API Status enum."""
    if value is None:
        return None

    normalized = value.strip().lower()
    mapping = {
        "to_do": Status.TO_DO,
        "todo": Status.TO_DO,
        "in_progress": Status.IN_PROGRESS,
        "in progress": Status.IN_PROGRESS,
        "completed": Status.COMPLETED,
        "done": Status.COMPLETED,
    }

    try:
        return mapping[normalized]
    except KeyError as exc:
        message = f"Unsupported status value: {value}"
        raise ValueError(message) from exc


def serialize_tool_result(result: object) -> str:
    """Convert a tool result into a compact string for model follow-up."""
    try:
        if hasattr(result, "model_dump"):
            return json.dumps(result.model_dump(), default=str)

        if isinstance(result, list):
            serialized_items: list[Any] = []
            for item in result:
                if hasattr(item, "model_dump"):
                    serialized_items.append(item.model_dump())
                elif hasattr(item, "__dict__"):
                    serialized_items.append(item.__dict__)
                else:
                    serialized_items.append(str(item))
            return json.dumps(serialized_items, default=str)

        if hasattr(result, "__dict__"):
            return json.dumps(result.__dict__, default=str)

        return json.dumps(result, default=str)
    except TypeError:
        return str(result)


def execute_tool( # noqa: PLR0911,C901
        client: Client,
        tool_name: str,
        arguments_json: str) -> tuple[object, str]:
    """Execute a tool against the shared issue-tracker client."""
    args = json.loads(arguments_json) if arguments_json else {}

    if tool_name == "get_boards":
        result = list(client.get_boards())
        return result, f"Retrieved {len(result)} board(s)."

    if tool_name == "get_board":
        board_id = args["board_id"]
        result = client.get_board(board_id)
        return result, f"Retrieved board {board_id}."

    if tool_name == "get_issues":
        board_id = args["board_id"]
        result = list(client.get_issues(board_id))
        return result, f"Retrieved {len(result)} issue(s) for board {board_id}."

    if tool_name == "get_issue":
        issue_id = args["issue_id"]
        result = client.get_issue(issue_id)
        return result, f"Retrieved issue {issue_id}."

    if tool_name == "create_issue":
        title = args["title"]
        board_id = args["board_id"]
        desc = args.get("desc")
        members = args.get("members")
        due_date = args.get("due_date")
        status = _parse_status(args.get("status")) or Status.TO_DO

        result = client.create_issue(
            title=title,
            board_id=board_id,
            desc=desc,
            members=members,
            due_date=due_date,
            status=status,
        )
        return result, f"Created issue '{title}' on board {board_id}."

    if tool_name == "update_issue":
        issue_id = args["issue_id"]
        title = args.get("title")
        desc = args.get("desc")
        members = args.get("members")
        due_date = args.get("due_date")
        status = _parse_status(args.get("status"))
        board_id = args.get("board_id")

        result = client.update_issue(
            issue_id=issue_id,
            title=title,
            desc=desc,
            members=members,
            due_date=due_date,
            status=status,
            board_id=board_id,
        )
        return result, f"Updated issue {issue_id}."

    if tool_name == "create_board":
        name = args["name"]
        result = client.create_board(name=name)
        return result, f"Created board '{name}'."

    if tool_name == "update_board":
        board_id = args["board_id"]
        name = args.get("name")
        result = client.update_board(board_id=board_id, name=name)
        return result, f"Updated board {board_id}."

    if tool_name == "delete_issue":
        issue_id = args["issue_id"]
        result = client.delete_issue(issue_id)
        return result, f"Deleted issue {issue_id}."

    if tool_name == "delete_board":
        board_id = args["board_id"]
        result = client.delete_board(board_id)
        return result, f"Deleted board {board_id}."
    message = f"Unknown tool: {tool_name}"
    raise ValueError(message)
