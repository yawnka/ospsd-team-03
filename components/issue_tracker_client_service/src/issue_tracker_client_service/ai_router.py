"""AI orchestration helpers for the issue tracker service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ai_client_api import get_client

if TYPE_CHECKING:
    from collections.abc import Callable

    from ai_client_api.client import AIClient
    from api.client import Client  # type: ignore[import-untyped]

from issue_tracker_client_service.ai_schemas import AIActionOut, AIChatIn, AIChatOut
from issue_tracker_client_service.ai_tools import (
    TOOLS,
    execute_tool,
    serialize_tool_result,
)


def _build_system_prompt() -> str:
    """Return the system prompt for the AI assistant."""
    return (
        "You are an AI assistant for an issue tracker service. "
        "You can inspect boards and issues, create issues and boards, "
        "update issues and boards, and delete issues and boards. "
        "When a user asks to perform one of these actions, prefer calling a tool. "
        "Do not invent IDs. "
        "Use the exact tool arguments when possible. "
        "Valid statuses are to_do, in_progress, and completed. "
        "Be concise and accurate."
    )


def run_ai_chat(
    payload: AIChatIn,
    issue_tracker_client: Client,
    ai_client: AIClient | None = None,
    on_tool_executed: Callable[[str, object, str], None] | None = None,
    ) -> AIChatOut:
    """Run the AI workflow for a chat request."""
    ai_client =ai_client or get_client()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": payload.message},
    ]

    first_response = cast(
        "Any",
        ai_client.create_chat_completion(
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        ),
    )

    first_message = first_response.choices[0].message
    tool_calls = first_message.tool_calls or []

    if not tool_calls:
        content = first_message.content or ""
        return AIChatOut(reply=content.strip(), actions=[])

    actions: list[AIActionOut] = []

    messages.append(
        {
            "role": "assistant",
            "content": first_message.content or "",
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in tool_calls
            ],
        }
    )

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        raw_result, detail = execute_tool(
            client=issue_tracker_client,
            tool_name=tool_name,
            arguments_json=tool_call.function.arguments,
        )

        actions.append(AIActionOut(tool=tool_name, detail=detail))
        if on_tool_executed is not None:
            on_tool_executed(tool_name, raw_result, detail)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": serialize_tool_result(raw_result),
            }
        )

    final_response = cast(
        "Any",
        ai_client.create_chat_completion(messages=messages),
        )

    final_message = final_response.choices[0].message
    final_text = (final_message.content or "").strip()

    if not final_text and actions:
        final_text = actions[-1].detail or "Action completed."

    return AIChatOut(reply=final_text, actions=actions)
