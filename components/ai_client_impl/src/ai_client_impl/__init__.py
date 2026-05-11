"""Register the OpenAI AI client implementation."""


from __future__ import annotations

import os

from ai_client_api import register
from ai_client_impl.client import DEFAULT_MODEL, OpenAIAIClient


def _factory() -> OpenAIAIClient:
    """Build the registered OpenAI AI client instance."""
    api_key = os.environ["OPENAI_API_KEY"]
    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
    return OpenAIAIClient(api_key=api_key, model=model)


register(_factory)
