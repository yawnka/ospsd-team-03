# issue_tracker_client_api

# DRAFT VERSION of what we might do

## Overview

This package defines the abstract interface for an issue tracker.

It contains:
- `Issue` and `Comment` data models
- `IssueTrackerClient` (an abstract base class)
- `register()` and `get_client()` for dependency injection

The API does not depend on Trello or any other provider.

---

## Interface

`IssueTrackerClient` defines:

- `list_issues(...)`
- `get_issue(...)`
- `create_issue(...)`
- `close_issue(...)`
- `add_comment(...)`

Any implementation must implement these methods.

---

## Dependency Injection

The API provides:

- `register(factory)`
- `get_client()`

`register()` installs an implementation.
`get_client()` returns an instance of the registered implementation.
