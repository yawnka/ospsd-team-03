# Issue Tracker Client API

## Overview
`issue_tracker_client_api` defines the `IssueTrackerClient` abstract base class that every issue tracker client must implement. The package contains the abstraction, immutable domain models, and a dependency-injection (`register` / `get_client`) hook, but no concrete provider logic.

## Purpose
- Document the operations available to consumers (list/get/create/close issues, and add comments)
- Provide a single factory (`get_client`) that implementations can override.
- Keep the API provider-agnostic by using only explicit domain models (`Issue`, `Comment`, `IssueState`)

## Architecture

### Component Design
The package exposes one abstract base class focused on issue-tracker operations:
- list issues for a board
- fetch a single issue
- create and close issues
- add a comment

It depends only on the `Issue`, `Comment`, and `IssueState` domain models defined in the same module. 

### API Integration
```python
from issue_tracker_client_api.client import IssueTrackerClient, get_client

client: IssueTrackerClient = get_client()
issues = client.list_issues("my_board")
for issue in issues:
    print(issue.id, issue.title)
```

### Dependency Injection
Implementation packages (for example `issue_tracker_client_impl`) register a concrete client factory at import time:

```python
import issue_tracker_client_impl  # registers a factory via issue_tracker_client_api.client.register

from issue_tracker_client_api.client import get_client

client = get_client()
```

## API Reference

### Domain Models
```python

class IssueState(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True)
class Issue:
    id: int
    title: str
    body: str
    state: IssueState

@dataclass(frozen=True)
class Comment:
    id: int
    body: str
```



### IssueTrackerClient Abstract Base Class
```python
class IssueTrackerClient(ABC):
    ...
```

#### Methods
- `list_issues(self, board: str) -> list[Issue]`: Return all open issues for `board`.
- `get_issue(self, board: str, issue_id: int) -> Issue`: Return a single issue by `issue_id`.
- `create_issue(self, board: str, title: str, body: str) -> Issue`: Create a new issue and return it.
- `close_issue(self, board: str, issue_id: int) -> bool`: Close the issue identified by `issue_id` and return `True` if successful.
- `add_comment(self, board: str, issue_id: int, body: str) -> Comment`: Add a comment and return it.

### Factory Function
- `register(factory: Callable[[], IssueTrackerClient]) -> None:`: Register (and replace) the active factory
- `get_client() -> IssueTrackerClient`: Return a client from the registered factory; raises `RuntimeError` if none registered

## Usage Examples

### Basic Operations
```python
from issue_tracker_client_api.client import get_client

client = get_client()
for issue in client.list_issues("my_board"):
    print(f"{issue.id}: {issue.title}")
```

### Creating an Issue + Commenting
```python
from issue_tracker_client_api.client import get_client

client = get_client()
created = client.create_issue(
    "my_board", 
    title="Bug: login fails", 
    body="Steps to reproduce..."
    )
client.add_comment("my_board", created.id, "I can reproduce this on macOS too.")
```

## Implementation Checklist
1. Implement every method in the abstract base class `IssueTrackerClient`.
2. Return `Issue` / `Comment` objects compatible with the dataclass models in this package
3. Register a factory at import time so that `get_client()` returns  concrete implementation automatically
4. Keep all provider SDK types and authentication details out of this interface package

## Testing
```bash
uv run pytest components/issue_tracker_client_api/tests/ -q
uv run pytest components/issue_tracker_client_api/tests/ --cov=components/issue_tracker_client_api/src/issue_tracker_client_api --cov-report=term-missing
```

