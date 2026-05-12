# Issue Tracker Client Implementation Trello

## Overview

`issue_tracker_client_impl` provides the Trello-backed implementation of the `issue_tracker_client_api.IssueTrackerClient` contract.

This package handles Trello authentication, performs Trello REST API calls, and converts Trello-specific boards, lists, and cards into provider-agnostic `Board`, `Issue`, and `Status` domain models.

Consumers should code against `issue_tracker_client_api`, not directly against this implementation package.

## Purpose

This component is responsible for:

- connecting to Trello through the Trello REST API,
- loading Trello credentials from environment variables,
- implementing every method in `IssueTrackerClient`,
- mapping Trello boards to `Board` objects,
- mapping Trello cards to `Issue` objects,
- mapping Trello lists to issue `Status` values,
- registering itself with the issue tracker API on import,
- keeping Trello-specific response shapes out of the interface package.

## Dependency Injection

Importing this package registers `DefaultIssueTrackerClient` with the issue tracker API factory.

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

client = get_client()
```

After registration, consumers can call `get_client()` and receive the Trello-backed implementation without directly constructing it.



## Authentication

Trello uses **API key** and **token authentication**.

### Required Environment Variables
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
Implements the `IssueTrackerClient` abstract base class.

#### Methods

- `get_issue(issue_id: str) -> Issue`: Fetch a single Trello card and convert it into an `Issue`.

- `get_board(board_id: str) -> Board`: Fetch a Trello board and convert it into a `Board`.

- `get_issues(board_id: str, status: Status | None = None) -> Iterator[Issue]`: Fetch issues from a Trello board, optionally filtered by status.

- `get_boards() -> Iterator[Board]`: Fetch boards accessible to the authenticated Trello user.

- `create_issue(title: str, board_id: str, desc: str | None = None, members: list[str] | None = None, due_date: str | None = None, status: Status = Status.TO_DO) -> Issue`: Create a Trello card and return it as an `Issue`.

- `create_board(name: str) -> Board`: Create a Trello board.

- `update_issue(issue_id: str, title: str | None = None, desc: str | None = None, members: list[str] | None = None, due_date: str | None = None, status: Status | None = None, board_id: str | None = None) -> Issue`: Update a Trello card.

- `update_board(board_id: str, name: str | None = None) -> Board`: Update a Trello board.

- `delete_issue(issue_id: str) -> bool`: Archive or delete a Trello card.

- `delete_board(board_id: str) -> bool`: Delete or close a Trello board.

## Usage Examples

### List Issues

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import Status, get_client

client = get_client()

for issue in client.get_issues("your_board_id", status=Status.TO_DO):
    print(issue.id, issue.title)
```

### Create an Issue

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import Status, get_client

client = get_client()

new_issue = client.create_issue(
    title="Fix CI pipeline",
    board_id="your_board_id",
    desc="CircleCI fails on mypy strict mode.",
    status=Status.TO_DO,
)

print(new_issue.id)
```

### Update an Issue

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import Status, get_client

client = get_client()

updated_issue = client.update_issue(
    issue_id="your_issue_id",
    status=Status.IN_PROGRESS,
)

print(updated_issue.status)
```

### Delete an Issue

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

client = get_client()

deleted = client.delete_issue("your_issue_id")
print(deleted)
```

### Error Handling

The implementation raises provider-agnostic exceptions from `issue_tracker_client_api` where appropriate.

Examples include:
- `IssueNotFoundError`
- `BoardNotFoundError`
- `IssueCreateError`

Provider-specific Trello errors should be translated before they cross the interface boundary.

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
        ```bash
        set -a && source .env && set +a
        ```
   

## Testing

Run this component's tests with:

```bash
uv run pytest components/issue_tracker_client_impl/tests/ -q
```

Run with coverage:

```bash
uv run pytest components/issue_tracker_client_impl/tests/ --cov=components/issue_tracker_client_impl/src/issue_tracker_client_impl --cov-report=term-missing
```

Unit tests should mock Trello API calls and remain fast, deterministic, and credential-free.

Credential-dependent integration or end-to-end tests require:
- `TRELLO_API_KEY`
- `TRELLO_API_TOKEN`
- `TRELLO_BOARD_ID`

If credentials are missing, tests fail fast or skip appropriately.

## Trello API Integration

### Base URL

```text
https://api.trello.com/1
```

### Trello Concepts

| Trello Concept   | Project Concept   |
| ---------------- | ----------------- |
| Board            | `Board`           |
| Card             | `Issue`           |
| List             | `Status`          |
| Card name        | Issue title       |
| Card description | Issue description |

### Endpoints Used

- `GET /members/me/boards`
- `GET /boards/{board_id}`
- `GET /boards/{board_id}/cards`
- `GET /cards/{card_id}`
- `POST /cards`
- `PUT /cards/{card_id}`
- `DELETE /cards/{card_id}` or card archive endpoint
- `POST /boards`
- `PUT /boards/{board_id}`
- `DELETE /boards/{board_id}` or board close endpoint

All requests include Trello credentials as request parameters:

```python
{"key": self._api_key, "token": self._api_token}
```