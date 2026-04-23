# AI Client API

## Overview

`ai_client_api` defines the provider-agnostic interface for AI chat completions. It follows the same interface/implementation pattern as `issue_tracker_client_api`: a pure-stdlib abstract package that concrete providers register against at import time.

Added in **HW3 (Second Submission)**.

## Interface

```python
class AIClient(ABC):
    @abstractmethod
    def send_message(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> str: ...
```

`context` is an optional free-form dict that implementations may use to pass conversation history, tool results, or domain data to the provider.

## Dependency Injection

The same `register` / `get_client` pattern from `issue_tracker_client_api` is used:

```python
from ai_client_api import get_client

# Concrete implementation registers itself on import:
import ai_client_impl  # noqa: F401

client = get_client()
reply = client.send_message("Summarize the open tickets.")
```

`register(factory)` stores a zero-argument callable. `get_client()` calls it and returns the instance. Only one implementation can be registered at a time — importing a second one overwrites the first.

## Credential Approach

AI provider credentials are passed via environment variables, never hardcoded. Each concrete implementation reads its own key (e.g., `OPENAI_API_KEY`). This was agreed upon within the Issue Tracker vertical (Teams 1, 3, 7) as the unified credential approach.

## Tool Calling

The `send_message` interface is intentionally minimal. Tool calling is handled at the implementation level — each provider decides how to pass tool schemas and execute calls. In `ai_client_impl`, the full OpenAI tool-calling loop (multi-turn, parallel tools) is implemented inside `send_message` when tools are configured via the service layer.

## No Provider Dependencies

This package has no dependencies on OpenAI, Anthropic, or any other provider SDK. It imports only Python stdlib (`abc`, `typing`).
