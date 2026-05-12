# AI Client API

`ai_client_api` defines the provider-agnostic contract for AI integrations.

The package contains the abstract `AIClient` interface plus a small dependency injection registry. Concrete AI providers, such as OpenAI, Claude, or Gemini implementations, register themselves behind this interface so application code can depend on the contract instead of a provider SDK.

## Purpose

This component is responsible for:

- defining the AI client abstraction,
- keeping provider SDK types out of the public interface,
- supporting simple chat-style prompts,
- supporting chat-completion workflows used by tool calling,
- providing `register()` and `get_client()` dependency injection helpers.

## Public Interface

The minimum interface is:

```python
send_message(prompt: str, context: dict[str, Any] | None = None) -> str
```

Implementations may also provide a chat-completion method used by the service's tool-calling pipeline, but consumers should still depend on `AIClient` rather than a concrete provider class.

## Dependency Injection

Provider implementations register themselves with this package. Consumers can then request the configured client through `get_client()`.

### Example 

```python
from ai_client_api import get_client

client = get_client()
response = client.send_message("Summarize this ticket.")
print(response)
```

A concrete implementation package, such as `ai_client_impl`, should be imported before `get_client()` is called if auto-registration is required:

```python
import ai_client_impl
from ai_client_api import get_client

client = get_client()
response = client.send_message("Create a short summary of open issues.")
print(response)
```


## Testing

Run this component's tests with:
```bash
uv run pytest components/ai_client_api/tests/
```
