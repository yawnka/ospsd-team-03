"""Tests for the OpenAI AI client implementation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from ai_client_impl.client import OpenAIAIClient

from ai_client_api import AIClientError


def test_send_message_returns_text_response() -> None:
    """send_message should return the stripped text from OpenAI."""
    fake_sdk_client = MagicMock()

    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = "  hello from model  "

    fake_sdk_client.chat.completions.create.return_value = fake_response

    client = OpenAIAIClient(api_key="test-key")
    client._client = fake_sdk_client

    result = client.send_message("hello")

    assert result == "hello from model"
    fake_sdk_client.chat.completions.create.assert_called_once()


def test_send_message_includes_context_in_system_message() -> None:
    """send_message should include context as a system message when provided."""
    fake_sdk_client = MagicMock()

    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = "done"

    fake_sdk_client.chat.completions.create.return_value = fake_response

    client = OpenAIAIClient(api_key="test-key")
    client._client = fake_sdk_client

    _ = client.send_message(
        "summarize this ticket",
        context={"ticket_id": "123", "board_id": "abc"},
    )

    call_kwargs = fake_sdk_client.chat.completions.create.call_args.kwargs
    messages = call_kwargs["messages"]

    assert messages[0]["role"] == "system"
    assert "ticket_id" in messages[0]["content"]
    assert "board_id" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "summarize this ticket"


def test_send_message_raises_when_response_has_no_content() -> None:
    """send_message should raise when the model returns no text content."""
    fake_sdk_client = MagicMock()

    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = None

    fake_sdk_client.chat.completions.create.return_value = fake_response

    client = OpenAIAIClient(api_key="test-key")
    client._client = fake_sdk_client

    with pytest.raises(AIClientError):
        client.send_message("hello")
