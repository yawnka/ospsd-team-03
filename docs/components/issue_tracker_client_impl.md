# Issue Tracker Client Implementation (Trello)

## Overview

This package is the default **Trello-backed** implementation of `issue_tracker_client_api.IssueTrackerClient`.

It:
- authenticates using Trello API key + token
- makes Trello REST API calls
- converts Trello responses into `Issue` / `Comment` domain models
- auto-registers itself via dependency injection on import

Users should code against `issue_tracker_client_api`, not this package.

## Dependency Injection Wiring
Importing this package registers `DefaultIssueTrackerClient` with the interface layer:

```python
import issue_tracker_client_impl  # triggers DI registration
from issue_tracker_client_api.client import get_client

client = get_client()
```

This ensures the implementation is resolved dynamically through the API layer without tight coupling.

## Authentication

### Required Environment Variables
```bash
export TRELLO_API_KEY="your_api_key"
export TRELLO_API_TOKEN="your_api_token"
export TRELLO_BOARD_ID="your_board_id"  # required for E2E tests
```

Notes:
- Credentials are read from environment variables (never hardcoded).
- The `board` argument is the **Trello board ID** (from the URL / API), not the board name.
- `issue_id` is the card’s **short numeric ID** (`idShort`); the implementation resolves it to the full Trello card ID internally.

## Operations
::: issue_tracker_client_impl.client
    options:
        show_root_heading: true
        show_source: false

## Usage Example
```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

client = get_client()
created = created = client.create_issue(
    "your_board_id",
    "Bug: login fails",
    "Steps to reproduce..."
)
client.add_comment("your_board_id",
    created.id,
    "Confirmed on macOS too."
)
```

## Testing
```bash
uv run pytest components/issue_tracker_client_impl/tests/ -q
```

Integration + E2E suites live under `tests/` and require Trello credentials.