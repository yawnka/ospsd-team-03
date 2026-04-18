"""OpenAI implementation of the shared AI client API."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from ai_client_api import AIClient, AIClientError


class OpenAIAIClient(AIClient):
    """Concrete AI client backed by the OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        """Initialize the OpenAI AI client.

        Args:
            api_key: OpenAI API key.
            model: Model name to use for chat completions.

        """
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

        if context is not None:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant for an issue tracker service. "
                        "Use the provided context when it is relevant.\n\n"
                        f"Context: {context}"
                    ),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )

        content = response.choices[0].message.content
        if content is None:
            msg = "OpenAI response did not contain any text content."
            raise AIClientError(msg)

        return content.strip()

    @property
    def client(self) -> OpenAI:
        """Return the underlying SDK client."""
        return self._client


    @property
    def model(self) -> str:
        """Return the model name."""
        return self._model
