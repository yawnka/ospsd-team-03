# Issue Tracker Client API

## Overview

`issue_tracker_client_api` defines the provider-agnostic issue tracker contract used by this repository. The package contains the `IssueTrackerClient` abstract base class, immutable domain models, domain-specific exceptions, and a dependency-injection hook through `register()` and `get_client()`.

This package contains no concrete provider logic. Trello-specific behavior belongs in `issue_tracker_client_impl`.

## Purpose

- Document the operations available to issue tracker consumers.
- Provide a stable `IssueTrackerClient` interface.
- Define provider-agnostic domain models such as `Board`, `Issue`, and `Status`.
- Provide a single factory, `get_client()`, that returns the registered implementation.
- Keep provider SDK types and authentication details out of the interface package.

## Architecture

### Component Design

The package exposes one abstract base class focused on issue tracker operations:

- get a single issue,
- get a single board,
- list issues on a board,
- list accessible boards,
- create an issue,
- create a board,
- update an issue,
- update a board,
- delete an issue,
- delete a board.

It depends only on the domain models and exceptions defined in the same package.

### API Integration

```python
from issue_tracker_client_api.client import IssueTrackerClient, Status, get_client

client: IssueTrackerClient = get_client()
issues = client.get_issues("my_board", status=Status.TO_DO)

for issue in issues:
    print(issue.id, issue.title)
```

### Dependency Injection

Implementation packages, such as `issue_tracker_client_impl`, register a concrete client factory at import time:

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import get_client

client = get_client()
```
Consumers call `get_client()` and depend on the abstract interface rather than a specific provider.

## API Reference

### Domain Models

```python
class Status(Enum):
    TO_DO = "to_do"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True)
class Board:
    id: str
    name: str


@dataclass(frozen=True)
class Issue:
    id: str
    board_id: str
    title: str
    desc: str
    status: Status
    members: list[str] | None = None
    due_date: str | None = None
```

### Domain Exceptions

```python
class IssueNotFoundError(Exception):
    ...


class BoardNotFoundError(Exception):
    ...


class IssueCreateError(Exception):
    ...
```

### IssueTrackerClient Abstract Base Class

```python
class IssueTrackerClient(ABC):
    ...
```

### Methods
- `get_issue(self, issue_id: str) -> Issue`: Return a single issue by ID.
- `get_board(self, board_id: str) -> Board`: Return a single board by ID.
- `get_issues(self, board_id: str, status: Status | None = None) -> Iterator[Issue]`: Return issues on a board, optionally filtered by status.
- `get_boards(self) -> Iterator[Board]`: Return boards accessible to the authenticated user.
- `create_issue(self, title: str, board_id: str, desc: str | None = None, members: list[str] | None = None, due_date: str | None = None, status: Status = Status.TO_DO) -> Issue`: Create a new issue.
- `create_board(self, name: str) -> Board`: Create a new board.
- `update_issue(self, issue_id: str, title: str | None = None, desc: str | None = None, members: list[str] | None = None, due_date: str | None = None, status: Status | None = None, board_id: str | None = None) -> Issue`: Update an issue.
- `update_board(self, board_id: str, name: str | None = None) -> Board`: Update a board.
- `delete_issue(self, issue_id: str) -> bool`: Archive or delete an issue.
- `delete_board(self, board_id: str) -> bool`: Delete a board.

### Factory Functions

- `register(factory: Callable[[], IssueTrackerClient]) -> None`: Register and replace the active factory.
- `get_client(interactive: bool = False) -> IssueTrackerClient`: Return a client from the registered factory. Raises `RuntimeError` if no factory has registered.

## Usage Examples
### Basic Operations

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import Status, get_client

client = get_client()

for issue in client.get_issues("my_board", status=Status.TO_DO):
    print(f"{issue.id}: {issue.title}")
```

### Creating an Issue

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import Status, get_client

client = get_client()

created = client.create_issue(
    title="Bug: login fails",
    board_id="my_board",
    desc="Steps to reproduce...",
    status=Status.TO_DO,
)

print(created.id)
```

### Updating an Issue

```python
import issue_tracker_client_impl
from issue_tracker_client_api.client import Status, get_client

client = get_client()

updated = client.update_issue(
    issue_id="issue_id",
    status=Status.IN_PROGRESS,
)

print(updated.status)
```

## Implementation Checklist

1. Implement every method in the abstract base class `IssueTrackerClient`.
2. Return `Board` and `Issue` objects compatible with the dataclass models in this package.
3. Use the shared `Status` enum for issue status values.
4. Raise the package's domain exceptions for not-found or create-failure cases.
5. Register a factory at import time so that `get_client()` returns a concrete implementation automatically.
6. Keep provider SDK types and authentication details out of this interface package.

## Testing

Run this component's tests with:

```bash
uv run pytest components/issue_tracker_client_api/tests/ -q
```

Run with coverage:

```bash
uv run pytest components/issue_tracker_client_api/tests/ \
  --cov=components/issue_tracker_client_api/src/issue_tracker_client_api \
  --cov-report=term-missing
```
