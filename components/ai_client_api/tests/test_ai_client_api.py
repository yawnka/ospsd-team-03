"""Tests for ai_client_api."""

from __future__ import annotations

from typing import Any

import pytest
from ai_client_api.client import (
    AIClient,
    AIClientNotRegisteredError,
    get_client,
    register,
)


class MockAIClient(AIClient):
    """Simple concrete AI client used for tests."""

    def send_message(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        if context:
            return f"{prompt} | context={context}"
        return prompt

    def create_chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
    ) -> object:
        """Return a fake chat completion object."""
        _ = messages
        _ = tools
        _ = tool_choice
        return object()


def test_get_client_returns_registered_client() -> None:
    """get_client should return an instance from the registered factory."""
    register(MockAIClient)

    client = get_client()

    assert isinstance(client, MockAIClient)
    assert client.send_message("hello") == "hello"


def test_register_replaces_previous_factory() -> None:
    """Register should replace the previously registered factory."""

    class FirstClient(AIClient):
        def send_message(
            self,
            _prompt: str,
            _context: dict[str, Any] | None = None,
        ) -> str:
            return "first"

        def create_chat_completion(
            self,
            messages: list[dict[str, Any]],
            tools: list[dict[str, Any]] | None = None,
            tool_choice: str | None = None,
        ) -> object:
            """Return a fake chat completion object."""
            _ = messages
            _ = tools
            _ = tool_choice
            return object()

    class SecondClient(AIClient):
        def send_message(
            self,
            _prompt: str,
            _context: dict[str, Any] | None = None,
        ) -> str:
            return "second"

        def create_chat_completion(
            self,
            messages: list[dict[str, Any]],
            tools: list[dict[str, Any]] | None = None,
            tool_choice: str | None = None,
        ) -> object:
            """Return a fake chat completion object."""
            _ = messages
            _ = tools
            _ = tool_choice
            return object()

    register(FirstClient)
    first = get_client()
    assert first.send_message("x") == "first"

    register(SecondClient)
    second = get_client()
    assert second.send_message("x") == "second"


def test_send_message_can_accept_context() -> None:
    """Concrete AI clients should accept optional context."""
    register(MockAIClient)

    client = get_client()

    result = client.send_message(
        "summarize this",
        context={"ticket_id": "123", "board_id": "abc"},
    )

    assert "summarize this" in result
    assert "ticket_id" in result
    assert "board_id" in result


def test_get_client_raises_when_nothing_registered(monkeypatch:
                                                    pytest.MonkeyPatch) -> None:
    """get_client should fail when no implementation is registered."""
    monkeypatch.setattr("ai_client_api.client._factory", None)

    with pytest.raises(AIClientNotRegisteredError):
        get_client()
