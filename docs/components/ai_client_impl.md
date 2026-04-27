# AI Client Implementation (OpenAI)

## Overview

`ai_client_impl` is the concrete OpenAI-backed implementation of `ai_client_api`. It uses `gpt-4o-mini` by default and registers itself automatically on import.

Added in **HW3 (Second Submission)**.

## Required Environment Variable

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |

## Usage

```python
import ai_client_impl  # triggers DI registration
from ai_client_api import get_client

client = get_client()
reply = client.send_message("List all open issues on board abc123.")
print(reply)
```

## Implementation Details

`OpenAIAIClient` wraps the OpenAI Python SDK. `send_message` sends the prompt as a `user` message and returns the model's text response. When called from the service layer (`ai_router.py`), tool schemas are injected and the implementation runs a full multi-turn tool-calling loop:

1. First completion — model may return tool calls instead of text.
2. Each tool call is dispatched to `execute_tool()` in `ai_tools.py`, which calls the issue tracker client directly.
3. Tool results are appended to the message history.
4. Second completion — model produces the final natural-language response.

This multi-turn approach means the AI can chain actions (e.g., "list boards, then create an issue on the first one") in a single user request.

## Tools Available

The service wires 10 domain tools to the AI:

| Tool | Action |
|------|--------|
| `get_boards` | List all boards |
| `get_board` | Get a single board |
| `create_board` | Create a board |
| `update_board` | Rename a board |
| `delete_board` | Delete a board |
| `get_issues` | List issues on a board |
| `get_issue` | Get a single issue |
| `create_issue` | Create an issue |
| `update_issue` | Update title/status/assignees |
| `delete_issue` | Archive an issue |

## Model Configuration

The default model is `gpt-4o-mini`. It can be overridden by setting `OPENAI_MODEL` before the client is instantiated.

## Auto-Registration

`__init__.py` calls `ai_client_api.register(lambda: OpenAIAIClient())` at import time. Importing `ai_client_impl` is the only step required to make `get_client()` return an OpenAI-backed instance.
