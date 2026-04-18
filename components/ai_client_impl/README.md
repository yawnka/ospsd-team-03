# AI Client Implementation - DRAFT

OpenAI-backed implementation of the shared `ai_client_api`.

This package registers an `AIClient` implementation that uses the OpenAI API.

## Required environment variable

- `OPENAI_API_KEY`

## Example

```python
import openai_ai_client_impl  # noqa: F401
from ai_client_api import get_client

client = get_client()
response = client.send_message("Summarize this ticket.")
print(response)
```