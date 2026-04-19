"""ai_client_api — abstract contract for an ai client."""

from ai_client_api.client import (
    AIClient,
    AIClientError,
    AIClientNotRegisteredError,
    get_client,
    register,
)

__all__ = [
    "AIClient",
    "AIClientError",
    "AIClientNotRegisteredError",
    "get_client",
    "register",
]
