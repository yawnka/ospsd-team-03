# Issue Tracker Client Implementation (Trello)

## Overview
`issue_tracker_client_impl` ships a concrete implementation of `issue_tracker_client_api.IssueTrackerClient` backed by the Trello REST API. It handles authentication, performs Trello API calls, and converts Trello-specific responses into the interface-defined `Issue` and `Comment` dataclasses.

## Purpose

This package serves as the Trello-backed implementation of the Issue Tracker abstraction:

- **Trello API Integration**: Connects to Trello using official Trello REST APIs
- **API Key Authentication**: Secure environment-variable based credential handling
- **ABC Implementation**: Implements all abstract methods from `IssueTrackerClient`
- **Dependency Injection**: Automatically registers itself as the Client implementation upon import
- **Clean Abstraction Boundary**: Trello-specific types never leak into the interface

Users always code against the interface (`issue_tracker_client_api`), not this implementation.

## Architecture

### Dependency Injection
Importing this package automatically injects the Trello client into the interface factory:
```python
import issue_tracker_client_impl  # triggers DI
from issue_tracker_client_api.client import get_client

client = get_client()
```

### Client Construction

This package does not expose a public factory function.

Instead, importing `issue_tracker_client_impl` registers `DefaultIssueTrackerClient` with the interface layer.

Client instances are created via:

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

client = get_client() 
```

### Authentication

Trello uses **API key** and **token authentication**.

#### Required Environment Variables
```bash
export TRELLO_API_KEY="your_api_key"
export TRELLO_API_TOKEN="your_api_token"
export TRELLO_BOARD_ID="your_board_id"  # required for E2E tests
```

-   `TRELLO_API_KEY` - Trello developer API key
-   `TRELLO_API_TOKEN` - User access token
-   `TRELLO_BOARD_ID` - Required for End-to-End (E2E) tests

`TRELLO_BOARD_ID` must be the ID of a Trello board your key/token has
access to.

The implementation:
- Reads credentials from environment variables
- Validates they exist at startup
- Attaches them to every Trello API request
- Raises `KeyError` exceptions if either is missing


## API Reference

### DefaultIssueTrackerClient
Implements the `issue_tracker_client_api.IssueTrackerClient` abstract base class.

#### Methods

- `list_issues(board: str) -> list[Issue]`: Fetches all open cards from a Trello board.
- `get_issue(board: str, issue_id: int) -> Issue`: Fetches a single Trello card by its **short numeric ID** (`idShort`), resolving it internally to the full Trello card ID.
- `create_issue(board: str, title: str, body: str) -> Issue`: Creates a new Trello card on a board in the first open list, and returns it.
- `close_issue(board: str, issue_id: int) -> bool`: Closes the issue identified by `issue_id` and returns `True` if successful.
- `add_comment(board: str, issue_id: int, body: str) -> Comment`: Adds a comment and return it.

The `board` parameter must be the Trello **board ID** (the identifier used in Trello URLs and API requests), not the human-readable board name.


## Usage Examples

### Basic Retrieval
```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

client = get_client()

issues = client.list_issues("your_board_id")

for issue in issues:
    print(issue.title)
```

### Creating a Trello Card
```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

client = get_client()

new_issue = client.create_issue(
    board="your_board_id",
    title="Fix CI pipeline",
    body="CircleCI fails on mypy strict mode."
)

print(new_issue.id)
```

### Add a Comment
```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

client = get_client()

new_comment = client.add_comment(
    board="your_board_id",
    issue_id=42,
    body="Check in with manager"
)
print(new_comment)
```

### Error Handling

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

try:
    client = get_client()
    # Attempt to get list of issues
    issues = client.list_issues("your_board_id")
    for issue in issues:
        print(issue.title)
    
except Exception as e:
    print(f"Error accessing Trello: {e}")
    # Handle authentication errors, network issues, etc.
```

## Authentication Setup

### Local Setup

1. **Environment Variables**:
   ```bash
   export TRELLO_API_KEY="your_api_key"
   export TRELLO_API_TOKEN="your_api_token"
   export TRELLO_BOARD_ID="your_board_id"
   ```

2. **CI/CD Integration**:
   - Set environment variables in CircleCI/GitHub Actions
   - No browser interaction required

### Credential Sources

1. **Environment Variables**
   - `TRELLO_API_KEY`
   - `TRELLO_API_TOKEN`
   - `TRELLO_BOARD_ID`

2. **Local `.env` File**
    -  Create an `.env` file in the root of this project and define: 
        ```text
        TRELLO_API_KEY=your_api_key
        TRELLO_API_TOKEN=your_api_token
        TRELLO_BOARD_ID=your_board_id
        ```
    -  Load the `.env` file:
        ``` bash
        set -a && source .env && set +a
        ```
   

## Testing
```bash
uv run pytest components/issue_tracker_client_impl/tests/ -q
uv run pytest components/issue_tracker_client_impl/tests/ --cov=components/issue_tracker_client_impl/src/issue_tracker_client_impl --cov-report=term-missing
```

#### Unit tests 
- Uses mocks
- No real Trello API calls
- Fast and deterministic

#### Integration and E2E tests 
E2E tests require:
- `TRELLO_API_KEY`
- `TRELLO_API_TOKEN`
- `TRELLO_BOARD_ID`

If credentials are missing, tests fail fast or skip appropriately

## Trello API Integration

### Base URL
```text
https://api.trello.com/1
```

### Endpoints Used

- `list_issues` -> `GET /boards/{board}/cards`
- `get_issue` -> `GET /cards/{card_id}`
- `create_issue` -> `GET /boards/{board}/lists`, `POST /cards`
- `close_issue` -> `PUT /cards/{card_id}`
- `add_comment` -> `POST /cards/{card_id}/actions/comments`

All requests include:

```python
{"key": self._api_key, "token": self._api_token}
```


