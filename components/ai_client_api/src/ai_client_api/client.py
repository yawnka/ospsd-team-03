"""Abstract contract and registry for AI clients."""

from __future__ import annotations

import abc
from collections.abc import Callable  # noqa: TC003
from typing import Any


class AIClientError(Exception):
    """Base exception for AI client errors."""


class AIClientNotRegisteredError(AIClientError):
    """Raised when no AI client implementation has been registered."""


class AIClient(abc.ABC):
    """Abstract interface for an AI client implementation."""

    @abc.abstractmethod
    def send_message(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Send a prompt to the AI model and return its response.

        Args:
            prompt: The user prompt to send to the model.
            context: Optional structured context to help guide the response.

        Returns:
            The model's response as a string.

        """
        raise NotImplementedError


_factory: Callable[[], AIClient] | None = None


def register(factory: Callable[[], AIClient]) -> None:
    """Register the active AI client factory.

    A concrete implementation package should call this during import.

    Args:
        factory: A zero-argument callable that returns an AIClient instance.

    """
    global _factory # noqa: PLW0603
    _factory = factory


def get_client() -> AIClient:
    """Return an instance of the registered AI client.

    Returns:
        A concrete AIClient instance.

    Raises:
        AIClientNotRegisteredError: If no implementation has been registered.

    """
    if _factory is None:
        msg = "No AI client implementation has been registered."
        raise AIClientNotRegisteredError(msg)
    return _factory()
