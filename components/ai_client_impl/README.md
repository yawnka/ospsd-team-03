# AI Client Implementation OpenAI

`ai_client_impl` provides the OpenAI-backed implementation of the shared `ai_client_api` contract.

This package registers an `AIClient` implementation that uses the OpenAI API. The service depends on the abstract AI client contract, while this package contains the provider-specific OpenAI wiring.

## Purpose

This component is responsible for:

- implementing the shared `AIClient` interface,
- loading OpenAI credentials from environment variables,
- calling OpenAI chat-completion APIs,
- supporting tool-calling workflows used by the service,
- keeping OpenAI-specific SDK details out of consumer code,
- registering itself with `ai_client_api` on import.

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key used by the provider implementation |

## Usage

Importing this package triggers dependency injection registration.

```python
import ai_client_impl
from ai_client_api import get_client

client = get_client()
response = client.send_message("Summarize this ticket.")
print(response)
```

## Tool Calling

The implementation supports the chat-completion flow used by the service's AI tool-calling pipeline. The service can provide tool definitions, receive tool calls from the model, validate the arguments, and execute real issue tracker actions.

Provider-specific OpenAI response objects should stay inside this implementation package. Other components should interact through the shared AI client interface.

## Testing

Run this component's tests with:

```bash
uv run pytest components/ai_client_impl/tests/
```

The tests should mock the OpenAI SDK or HTTP boundary. Unit tests should not make real OpenAI network calls.