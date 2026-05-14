"""OpenAI implementation of the shared AI client API."""
from typing import Any, cast

from ai_client_api.client import AIClient, AIClientError
from openai import OpenAI

DEFAULT_MODEL = "gpt-4o-mini"

class OpenAIAIClient(AIClient):
    """Concrete AI client backed by the OpenAI API."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        """Initialize the OpenAI AI client."""
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def send_message(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Send a prompt to OpenAI and return the model response.

        Args:
            prompt: User prompt.
            context: Optional structured context.

        Returns:
            Model response text.

        Raises:
            AIClientError: If the model returns no text content.

        """
        messages: list[dict[str, str]] = []

        if context:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant for an issue tracker service.\n"
                        f"Context: {context}"
                    ),
                }
            )

        messages.append({"role": "user", "content": prompt})

        response = cast("Any", self.create_chat_completion(messages=messages))

        content = response.choices[0].message.content
        if not content:
            msg = "OpenAI response did not contain text content."
            raise AIClientError(msg)

        return str(content).strip()

    def create_chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
    ) -> object:
        """Create a chat completion using the private OpenAI SDK client."""
        if tools is None:
            return self._client.chat.completions.create(
                model=self._model,
                messages=cast("Any", messages),
            )

        return self._client.chat.completions.create(
            model=self._model,
            messages=cast("Any", messages),
            tools=cast("Any", tools),
            tool_choice=cast("Any", tool_choice),
        )
