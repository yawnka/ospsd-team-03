# AI Client Implementation (OpenAI)

OpenAI-backed implementation of the shared `ai_client_api`.

This package registers an `AIClient` implementation that uses the OpenAI API (GPT-4o-mini by default).

## Required environment variable

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |

## Example

```python
import ai_client_impl  # triggers DI registration
from ai_client_api import get_client

client = get_client()
response = client.send_message("Summarize this ticket.")
print(response)
```