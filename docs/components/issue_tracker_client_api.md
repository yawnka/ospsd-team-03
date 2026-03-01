# Issue Tracker Client API

## Overview

This package defines the provider-agnostic **interface** for an issue tracker client.

It includes:  

- Immutable domain models: `Issue`, `Comment`, `IssueState` 
- `IssueTrackerClient` abstract base class (ABC)
- A tiny dependency-injection hook: `register()` / `get_client()`

This package has **no Trello (or other provider) dependencies**.

## Purpose
- Keep the public contract small and stable
- Allow multiple implementations (Trello now, others later)
- Make testing easy by mocking the interface


## Architecture

### Component Design
`IssueTrackerClient` focuses on a minimal set of operations:
- list issues for a board
- fetch a single issue
- create and close issues
- add a comment

All inputs/outputs use only the domain models in this package.

### Dependency Injection
Implementation packages register a factory at import time:

```python
import issue_tracker_client_impl  # registers a factory via issue_tracker_client_api.client.register
from issue_tracker_client_api.client import get_client

client = get_client()
```

If no factory is registered, `get_client()` raises `RuntimeError`.


## API Reference
::: issue_tracker_client_api.client
    options:
        show_root_heading: true
        show_source: false

## Usage Examples

### Basic Listing
```python
from issue_tracker_client_api.client import get_client

client = get_client()
for issue in client.list_issues("my_board"):
    print(issue.id, issue.title)
```

## Testing
```bash
uv run pytest components/issue_tracker_client_api/tests/ -q
```
