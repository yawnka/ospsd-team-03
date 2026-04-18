# AI Client API - DRAFT

Shared abstract API for AI client integrations.

This package defines the abstract `AIClient` interface and a small
registration/factory mechanism so concrete implementations
(e.g. OpenAI, Claude, Gemini) can register themselves.

## Interface

```python
send_message(prompt: str, context: dict[str, Any] | None = None) -> str
```

#### Example 
```python 
from ai_client_api import get_client

client = get_client()
response = client.send_message("Summarize this ticket.")
print(response)
```